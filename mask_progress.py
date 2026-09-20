"""Transient terminal feedback; never part of the result protocol or task state."""
from contextlib import contextmanager
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
        self.started = self.last = time.monotonic()
        self.thread = threading.Thread(target=self.heartbeat, daemon=True)

    def write(self, text):
        self.stream.write(present.paint(text + '\n', self.stream, tone='progress'))
        self.stream.flush()

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
        with reporter.lock:
            reporter.label = None
    yield
