"""Windows Git process containment using documented Job and thread APIs."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import threading
import time

CREATE_SUSPENDED = 0x00000004


class BasicLimits(ctypes.Structure):
    _fields_ = [('PerProcessUserTimeLimit', ctypes.c_longlong),
                ('PerJobUserTimeLimit', ctypes.c_longlong), ('LimitFlags', w.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t), ('MaximumWorkingSetSize', ctypes.c_size_t),
                ('ActiveProcessLimit', w.DWORD), ('Affinity', ctypes.c_size_t),
                ('PriorityClass', w.DWORD), ('SchedulingClass', w.DWORD)]


class IOCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in
                ('ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount',
                 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [('BasicLimitInformation', BasicLimits), ('IoInfo', IOCounters),
                ('ProcessMemoryLimit', ctypes.c_size_t), ('JobMemoryLimit', ctypes.c_size_t),
                ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_longlong) for name in
                ('TotalUserTime', 'TotalKernelTime', 'ThisPeriodTotalUserTime', 'ThisPeriodTotalKernelTime')]
    _fields_ += [(name, w.DWORD) for name in
                 ('TotalPageFaultCount', 'TotalProcesses', 'ActiveProcesses', 'TotalTerminatedProcesses')]


class ThreadEntry(ctypes.Structure):
    _fields_ = [('dwSize', w.DWORD), ('cntUsage', w.DWORD), ('th32ThreadID', w.DWORD),
                ('th32OwnerProcessID', w.DWORD), ('tpBasePri', w.LONG),
                ('tpDeltaPri', w.LONG), ('dwFlags', w.DWORD)]


_spawn = threading.local()
_wrap = threading.Lock()


def recorded_spawn(start):
    """Run ``start`` (one ``Popen``) and return its process with the primary thread id ``CreateProcess`` gave it.

    ``Popen`` closes that thread's handle and drops its id. Without the id, finding the thread means walking a
    snapshot of every thread on the machine, which costs tens of milliseconds per spawn. The id is None when
    this Python's ``subprocess`` does not start processes through ``_winapi.CreateProcess``.
    """
    import _winapi
    with _wrap:
        if not getattr(_winapi.CreateProcess, 'mask_records_thread', False):
            create = _winapi.CreateProcess
            def recording(*args, **kwargs):
                result = create(*args, **kwargs)
                if getattr(_spawn, 'active', False):
                    _spawn.thread = result[3]  # (process handle, thread handle, process id, thread id)
                return result
            recording.mask_records_thread = True
            _winapi.CreateProcess = recording
    _spawn.thread, _spawn.active = None, True
    try:
        process = start()
    finally:
        _spawn.active = False
    return process, _spawn.thread


class WindowsJob:
    """Assign a suspended process before resuming its sole primary thread.

    Failure leaves the caller responsible for terminating the suspended process.
    There is no uncontained fallback, breakaway flag, or privilege adjustment.
    """

    def __init__(self):
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        declarations = {
            'CreateJobObjectW': ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            'SetInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
            'TerminateJobObject': ([w.HANDLE, w.UINT], w.BOOL),
            'QueryInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            'CreateToolhelp32Snapshot': ([w.DWORD, w.DWORD], w.HANDLE),
            'Thread32First': ([w.HANDLE, ctypes.POINTER(ThreadEntry)], w.BOOL),
            'Thread32Next': ([w.HANDLE, ctypes.POINTER(ThreadEntry)], w.BOOL),
            'OpenThread': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            'ResumeThread': ([w.HANDLE], w.DWORD),
            'GetProcessIdOfThread': ([w.HANDLE], w.DWORD),
            'CloseHandle': ([w.HANDLE], w.BOOL),
        }
        for name, (arguments, result) in declarations.items():
            function = getattr(self.api, name)
            function.argtypes, function.restype = arguments, result
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x00002000  # KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.get_last_error()
            self.close()
            raise ctypes.WinError(error)

    def start(self, pid, thread_id=None):
        """Assign the suspended process, then resume its primary thread: the one ``recorded_spawn`` captured, else the sole one found."""
        process = self.api.OpenProcess(0x0100 | 0x0001, False, pid)  # SET_QUOTA | TERMINATE
        if not process:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.api.AssignProcessToJobObject(self.handle, process):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.api.CloseHandle(process)
        if thread_id is None:
            thread_id = self.sole_thread(pid)
        thread = self.api.OpenThread(0x0002 | 0x0800, False, thread_id)  # SUSPEND_RESUME | QUERY_LIMITED_INFORMATION
        if not thread:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if self.api.GetProcessIdOfThread(thread) != pid:
                raise OSError('The primary thread does not belong to the contained process.')
            if self.api.ResumeThread(thread) != 1:
                raise OSError('Could not resume the contained primary thread.')
        finally:
            self.api.CloseHandle(thread)

    def sole_thread(self, pid):
        """The one thread of a suspended process, from a snapshot of every thread on the machine."""
        snapshot = self.api.CreateToolhelp32Snapshot(0x00000004, 0)  # SNAPTHREAD
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        threads = []
        try:
            entry = ThreadEntry()
            entry.dwSize = ctypes.sizeof(entry)
            found = self.api.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.th32OwnerProcessID == pid:
                    threads.append(entry.th32ThreadID)
                entry.dwSize = ctypes.sizeof(entry)
                found = self.api.Thread32Next(snapshot, ctypes.byref(entry))
            if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.api.CloseHandle(snapshot)
        if len(threads) != 1:
            raise OSError('Expected one suspended primary thread.')
        return threads[0]

    def stop(self):
        if not self.api.TerminateJobObject(self.handle, 1):
            raise ctypes.WinError(ctypes.get_last_error())
        deadline = time.monotonic() + 10
        while True:
            accounting = Accounting()
            if not self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
                raise ctypes.WinError(ctypes.get_last_error())
            if accounting.ActiveProcesses == 0:
                return
            if time.monotonic() >= deadline:
                raise OSError('Job processes did not terminate within the cleanup deadline.')
            time.sleep(0.01)

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None
