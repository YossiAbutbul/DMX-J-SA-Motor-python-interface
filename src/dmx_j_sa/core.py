"""High-level Python wrapper for Arcus DMX-J-SA integrated step motor.

Implements every interactive ASCII command listed in §10 of the
DMX-J-SA Manual rev 1.10. Communication uses PerformaxCom.dll (USB 2.0).

Typical usage:
    with DmxJsa.open_first() as m:
        m.enable(True)
        m.high_speed = 5000
        m.low_speed = 500
        m.acceleration = 300
        m.move_absolute(10000)
        m.wait_until_idle()
"""
from __future__ import annotations

import time
from enum import IntEnum, IntFlag
from typing import Optional

from .performax import PerformaxDLL, PerformaxError


class DmxError(PerformaxError):
    """Raised when DMX-J-SA returns an error reply (starts with '?')."""


class MotorStatus(IntFlag):
    CONST_SPEED = 1 << 0
    ACCEL = 1 << 1
    DECEL = 1 << 2
    HOME_INPUT = 1 << 3
    MINUS_LIMIT_INPUT = 1 << 4
    PLUS_LIMIT_INPUT = 1 << 5
    MINUS_LIMIT_ERROR = 1 << 6
    PLUS_LIMIT_ERROR = 1 << 7
    COMM_TIMEOUT_ALARM = 1 << 10


class MoveMode(IntEnum):
    ABS = 0
    INC = 1


class ProgramState(IntEnum):
    IDLE = 0
    RUNNING = 1
    PAUSED = 2
    ERROR = 4


class PolarityBit(IntFlag):
    DIRECTION = 1 << 0
    LIMIT = 1 << 1
    HOME = 1 << 2
    DIGITAL_OUTPUT = 1 << 3
    DIGITAL_INPUT = 1 << 4
    ENABLE_OUTPUT = 1 << 5
    JUMP_LINE0_ON_ERROR = 1 << 6


class DmxJsa:
    PRODUCT_ID = "DMX-J-SA-USB"

    def __init__(self, device_index: int = 0, dll: Optional[PerformaxDLL] = None,
                 read_timeout_ms: int = 1000, write_timeout_ms: int = 1000):
        self._dll = dll or PerformaxDLL()
        self._dll.set_timeouts(read_timeout_ms, write_timeout_ms)
        self._handle = self._dll.open(device_index)
        try:
            self._dll.flush(self._handle)
        except PerformaxError:
            pass

    @classmethod
    def open_first(cls, **kw) -> "DmxJsa":
        dll = PerformaxDLL()
        if dll.num_devices() == 0:
            raise DmxError("No Performax USB devices found")
        return cls(device_index=0, dll=dll, **kw)

    @staticmethod
    def list_devices() -> list[str]:
        dll = PerformaxDLL()
        return [dll.product_string(i) for i in range(dll.num_devices())]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self) -> None:
        if self._handle is not None:
            try:
                self._dll.close(self._handle)
            finally:
                self._handle = None

    def send(self, command: str) -> str:
        reply = self._dll.send_recv(self._handle, command)
        if reply.startswith("?"):
            raise DmxError(f"{command!r} -> {reply!r}")
        return reply

    def query_int(self, command: str) -> int:
        return int(self.send(command))

    def _set(self, command: str, value) -> None:
        reply = self.send(f"{command}={value}")
        if reply != "OK":
            raise DmxError(f"{command}={value} -> {reply!r}")

    @property
    def firmware_version(self) -> str:
        return self.send("VER")

    @property
    def product_id(self) -> str:
        return self.send("ID")

    @property
    def device_name(self) -> str:
        return self.send("DN")

    @device_name.setter
    def device_name(self, value: int) -> None:
        self._set("DN", int(value))

    @property
    def position(self) -> int:
        return self.query_int("PX")

    @position.setter
    def position(self, value: int) -> None:
        self._set("PX", int(value))

    @property
    def move_mode(self) -> MoveMode:
        return MoveMode(self.query_int("MM"))

    def set_absolute_mode(self) -> None:
        self.send("ABS")

    def set_incremental_mode(self) -> None:
        self.send("INC")

    @property
    def high_speed(self) -> int:
        return self.query_int("HSPD")

    @high_speed.setter
    def high_speed(self, pps: int) -> None:
        self._set("HSPD", int(pps))

    @property
    def low_speed(self) -> int:
        return self.query_int("LSPD")

    @low_speed.setter
    def low_speed(self, pps: int) -> None:
        self._set("LSPD", int(pps))

    @property
    def acceleration(self) -> int:
        return self.query_int("ACC")

    @acceleration.setter
    def acceleration(self, ms: int) -> None:
        self._set("ACC", int(ms))

    @property
    def run_current(self) -> int:
        return self.query_int("CUR")

    @run_current.setter
    def run_current(self, ma: int) -> None:
        self._set("CUR", int(ma))

    @property
    def idle_current(self) -> int:
        return self.query_int("ACR")

    @idle_current.setter
    def idle_current(self, ma: int) -> None:
        self._set("ACR", int(ma))

    @property
    def actual_current(self) -> int:
        return self.query_int("CCR")

    @property
    def idle_time(self) -> int:
        """Idle time in centiseconds before switching to idle current."""
        return self.query_int("ICN")

    @idle_time.setter
    def idle_time(self, cs: int) -> None:
        self._set("ICN", int(cs))

    def move_absolute(self, position: int) -> None:
        reply = self.send(f"X{int(position)}")
        if reply != "OK":
            raise DmxError(f"X{position} -> {reply!r}")

    def move(self, value: int) -> None:
        """Move using current move mode (ABS or INC). Command format: X<value> (no '=')."""
        reply = self.send(f"X{int(value)}")
        if reply != "OK":
            raise DmxError(f"X{value} -> {reply!r}")

    def jog_positive(self) -> None:
        self.send("J+")

    def jog_negative(self) -> None:
        self.send("J-")

    def home_positive(self) -> None:
        self.send("H+")

    def home_negative(self) -> None:
        self.send("H-")

    def home_hl_positive(self) -> None:
        self.send("HL+")

    def home_hl_negative(self) -> None:
        self.send("HL-")

    def limit_home_positive(self) -> None:
        self.send("L+")

    def limit_home_negative(self) -> None:
        self.send("L-")

    def stop(self) -> None:
        """Decelerated stop."""
        self.send("STOP")

    def abort(self) -> None:
        """Immediate stop, no decel."""
        self.send("ABORT")

    def clear_error(self) -> None:
        self.send("CLR")

    @property
    def status(self) -> MotorStatus:
        return MotorStatus(self.query_int("MST"))

    def is_moving(self) -> bool:
        return bool(self.status & (
            MotorStatus.CONST_SPEED | MotorStatus.ACCEL | MotorStatus.DECEL
        ))

    def wait_until_idle(self, poll_s: float = 0.02, timeout_s: Optional[float] = None) -> None:
        t0 = time.monotonic()
        while self.is_moving():
            if timeout_s is not None and time.monotonic() - t0 > timeout_s:
                raise DmxError("wait_until_idle: timeout")
            time.sleep(poll_s)

    def enable(self, on: bool = True) -> None:
        self._set("EO", 1 if on else 0)

    @property
    def enabled(self) -> bool:
        return self.query_int("EO") == 1

    @property
    def digital_inputs(self) -> int:
        return self.query_int("DI")

    def digital_input(self, idx: int) -> int:
        if not 1 <= idx <= 5:
            raise ValueError("DI index must be 1..5")
        return self.query_int(f"DI{idx}")

    @property
    def digital_outputs(self) -> int:
        return self.query_int("DO")

    @digital_outputs.setter
    def digital_outputs(self, value: int) -> None:
        self._set("DO", int(value) & 0x3)

    def set_digital_output(self, idx: int, value: int) -> None:
        if not 1 <= idx <= 2:
            raise ValueError("DO index must be 1..2")
        self._set(f"DO{idx}", 1 if value else 0)

    def get_digital_output(self, idx: int) -> int:
        if not 1 <= idx <= 2:
            raise ValueError("DO index must be 1..2")
        return self.query_int(f"DO{idx}")

    @property
    def do_boot(self) -> int:
        return self.query_int("DOBOOT")

    @do_boot.setter
    def do_boot(self, value: int) -> None:
        self._set("DOBOOT", int(value))

    @property
    def eo_boot(self) -> int:
        return self.query_int("EOBOOT")

    @eo_boot.setter
    def eo_boot(self, value: int) -> None:
        self._set("EOBOOT", int(value))

    @property
    def disable_limit(self) -> bool:
        return self.query_int("DL") == 1

    @disable_limit.setter
    def disable_limit(self, value: bool) -> None:
        self._set("DL", 1 if value else 0)

    @property
    def home_correction_amount(self) -> int:
        return self.query_int("HCA")

    @home_correction_amount.setter
    def home_correction_amount(self, value: int) -> None:
        self._set("HCA", int(value))

    @property
    def limit_correction_amount(self) -> int:
        return self.query_int("LCA")

    @limit_correction_amount.setter
    def limit_correction_amount(self, value: int) -> None:
        self._set("LCA", int(value))

    @property
    def polarity(self) -> PolarityBit:
        return PolarityBit(self.query_int("POL"))

    @polarity.setter
    def polarity(self, value: int) -> None:
        self._set("POL", int(value))

    @property
    def comm_timeout(self) -> int:
        """Watchdog timeout in ms. 0 disables."""
        return self.query_int("TOC")

    @comm_timeout.setter
    def comm_timeout(self, ms: int) -> None:
        self._set("TOC", int(ms))

    def get_variable(self, idx: int) -> int:
        if not 0 <= idx <= 49:
            raise ValueError("variable index must be 0..49")
        return self.query_int(f"V{idx}")

    def set_variable(self, idx: int, value: int) -> None:
        if not 0 <= idx <= 49:
            raise ValueError("variable index must be 0..49")
        self._set(f"V{idx}", int(value))

    def call_subroutine(self, num: int) -> None:
        if not 0 <= num <= 31:
            raise ValueError("subroutine must be 0..31")
        self.send(f"GS{num}")

    def program_state(self, program: int = 0) -> ProgramState:
        if program not in (0, 1):
            raise ValueError("program must be 0 or 1")
        return ProgramState(self.query_int(f"SASTAT{program}"))

    def program_counter(self, program: int = 0) -> int:
        if program not in (0, 1):
            raise ValueError("program must be 0 or 1")
        return self.query_int(f"SPC{program}")

    def program_run(self, program: int = 0) -> None:
        self._set(f"SR{program}", 1)

    def program_stop(self, program: int = 0) -> None:
        self._set(f"SR{program}", 0)

    def program_pause(self, program: int = 0) -> None:
        self._set(f"SR{program}", 2)

    def program_continue(self, program: int = 0) -> None:
        self._set(f"SR{program}", 3)

    @property
    def sload(self) -> int:
        return self.query_int("SLOAD")

    @sload.setter
    def sload(self, value: int) -> None:
        self._set("SLOAD", int(value))

    def get_program_line(self, line: int) -> str:
        if not 0 <= line <= 1274:
            raise ValueError("line must be 0..1274")
        return self.send(f"SA{line}")

    def set_program_line(self, line: int, value: int) -> None:
        if not 0 <= line <= 1274:
            raise ValueError("line must be 0..1274")
        self._set(f"SA{line}", int(value))

    def store_to_flash(self) -> None:
        self.send("STORE")
