"""Low-level ctypes wrapper around Arcus PerformaxCom.dll (USB)."""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from pathlib import Path


BUFFER_SIZE = 64


class PerformaxError(Exception):
    pass


class PerformaxDLL:
    def __init__(self, dll_path: str = "PerformaxCom.dll"):
        p = Path(dll_path)
        if not p.is_absolute():
            here = Path(__file__).resolve().parent
            for cand in (here / "dlls" / p.name, here / p.name):
                if cand.exists():
                    p = cand
                    break
        if hasattr(os, "add_dll_directory") and p.is_absolute() and p.exists():
            os.add_dll_directory(str(p.parent))
        self._dll = ctypes.WinDLL(str(p))

        self._dll.fnPerformaxComGetNumDevices.argtypes = [ctypes.POINTER(wintypes.DWORD)]
        self._dll.fnPerformaxComGetNumDevices.restype = wintypes.BOOL

        self._dll.fnPerformaxComGetProductString.argtypes = [
            wintypes.DWORD, ctypes.c_char_p, wintypes.DWORD,
        ]
        self._dll.fnPerformaxComGetProductString.restype = wintypes.BOOL

        self._dll.fnPerformaxComOpen.argtypes = [
            wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE),
        ]
        self._dll.fnPerformaxComOpen.restype = wintypes.BOOL

        self._dll.fnPerformaxComClose.argtypes = [wintypes.HANDLE]
        self._dll.fnPerformaxComClose.restype = wintypes.BOOL

        self._dll.fnPerformaxComSetTimeouts.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self._dll.fnPerformaxComSetTimeouts.restype = wintypes.BOOL

        self._dll.fnPerformaxComSendRecv.argtypes = [
            wintypes.HANDLE, ctypes.c_char_p, wintypes.DWORD,
            wintypes.DWORD, ctypes.c_char_p,
        ]
        self._dll.fnPerformaxComSendRecv.restype = wintypes.BOOL

        try:
            self._dll.fnPerformaxComFlush.argtypes = [wintypes.HANDLE]
            self._dll.fnPerformaxComFlush.restype = wintypes.BOOL
            self._has_flush = True
        except AttributeError:
            self._has_flush = False

    def num_devices(self) -> int:
        n = wintypes.DWORD(0)
        if not self._dll.fnPerformaxComGetNumDevices(ctypes.byref(n)):
            raise PerformaxError("GetNumDevices failed")
        return n.value

    def product_string(self, device_index: int, option: int = 0) -> str:
        buf = ctypes.create_string_buffer(BUFFER_SIZE)
        opt_param = (option << 8) | (device_index & 0xFF)
        if not self._dll.fnPerformaxComGetProductString(
            wintypes.DWORD(device_index), buf, wintypes.DWORD(opt_param)
        ):
            raise PerformaxError(f"GetProductString failed (idx={device_index})")
        return buf.value.decode("ascii", errors="replace")

    def open(self, device_index: int) -> int:
        h = wintypes.HANDLE()
        if not self._dll.fnPerformaxComOpen(wintypes.DWORD(device_index), ctypes.byref(h)):
            err = ctypes.get_last_error() or ctypes.GetLastError()
            raise PerformaxError(
                f"Open failed (idx={device_index}, GetLastError={err}). "
                "Likely: device already opened by another app (close Arcus GUI / "
                "SA_Download_Upload / prior Python session), or driver not bound."
            )
        return h.value

    def close(self, handle: int) -> None:
        if not self._dll.fnPerformaxComClose(wintypes.HANDLE(handle)):
            raise PerformaxError("Close failed")

    def set_timeouts(self, read_ms: int, write_ms: int) -> None:
        if not self._dll.fnPerformaxComSetTimeouts(
            wintypes.DWORD(read_ms), wintypes.DWORD(write_ms)
        ):
            raise PerformaxError("SetTimeouts failed")

    def send_recv(self, handle: int, command: str) -> str:
        wbuf = ctypes.create_string_buffer(BUFFER_SIZE)
        rbuf = ctypes.create_string_buffer(BUFFER_SIZE)
        cmd_bytes = command.encode("ascii")
        if len(cmd_bytes) >= BUFFER_SIZE:
            raise PerformaxError("Command too long for 64-byte buffer")
        wbuf.value = cmd_bytes
        if not self._dll.fnPerformaxComSendRecv(
            wintypes.HANDLE(handle), wbuf, BUFFER_SIZE, BUFFER_SIZE, rbuf
        ):
            raise PerformaxError(f"SendRecv failed (cmd={command!r})")
        return rbuf.value.decode("ascii", errors="replace")

    def flush(self, handle: int) -> None:
        if not self._has_flush:
            return
        if not self._dll.fnPerformaxComFlush(wintypes.HANDLE(handle)):
            raise PerformaxError("Flush failed")
