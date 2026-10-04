"""Transient terminal feedback; never part of the result protocol or task state."""
from contextlib import contextmanager
import os
import sys
import threading
import time

import mask_present as present

_active = None


class Reporter:
    def __init__(self, stream, interval=10):
        self.stream, self.interval = stream, interval
        self.stopped = threading.Event()
        self.lock = threading.Lock()
        self.label = None
        self.width = 0
        self.started = self.last = time.monotonic()
        self.thread = threading.Thread(target=self.heartbeat, daemon=True)

    def write(self, text):
        # Overwrite the previous status without ANSI cursor commands, including
        # when NO_COLOR is set. Consent and final output clear this line first.
        try:
            columns = os.get_terminal_size(self.stream.fileno()).columns or 80
        except (AttributeError, OSError, ValueError):
            columns = 80
        limit = max(20, columns - 1)
        if len(text) > limit:
            tail = min(24, limit // 2)
            text = text[:limit - tail - 3] + '...' + text[-tail:]
        padding = ' ' * max(0, self.width - len(text))
        self.stream.write('\r' + present.paint(text, self.stream, tone='progress') + padding)
        self.width = len(text)
        self.stream.flush()

    def clear(self):
        with self.lock:
            self.label = None
            if self.width:
                self.stream.write('\r' + ' ' * self.width + '\r')
                self.stream.flush()
                self.width = 0

    def phase(self, label):
        with self.lock:
            self.label = present.clean(label)
            self.started = self.last = time.monotonic()
            self.write('  ' + self.label + '...')

    def heartbeat(self):
        while not self.stopped.wait(min(self.interval, 1)):
            with self.lock:
                now = time.monotonic()
                if self.label and now - self.last >= self.interval:
                    self.write(f'  {self.label}... {int(now - self.started)}s')
                    self.last = now


@contextmanager
def reporting(enabled, label, *, stream=None, interval=10):
    global _active
    stream = sys.stderr if stream is None else stream
    previous = _active
    reporter = Reporter(stream, interval) if enabled and stream.isatty() else None
    _active = reporter
    try:
        if reporter:
            reporter.phase(label)
            reporter.thread.start()
        yield
    finally:
        if reporter:
            reporter.stopped.set()
            if reporter.thread.ident is not None:
                reporter.thread.join()
            reporter.clear()
        _active = previous


def phase(label, *, root=None):
    if _active:
        if root is not None:
            label += ' in ' + present.clean(root)
        _active.phase(label)


@contextmanager
def paused():
    reporter = _active
    if reporter:
        reporter.clear()
    yield
