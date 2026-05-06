# DMX-J-SA Python API Reference

Complete reference for `DmxJsa` (in `dmx_j_sa.py`). Every method maps 1:1 to an ASCII command from §10 of the DMX-J-SA manual.

```python
from dmx_j_sa import DmxJsa, MotorStatus, MoveMode, ProgramState, PolarityBit
```

---

## Class `DmxJsa`

### Construction

```python
DmxJsa(device_index=0, dll=None, read_timeout_ms=1000, write_timeout_ms=1000)
```
Open USB device by index. Bundled DLLs in `dlls/` auto-load.

```python
DmxJsa.open_first(**kw) -> DmxJsa          # opens index 0
DmxJsa.list_devices() -> list[str]         # product strings of all Performax USB devices
m.close()                                  # release handle (also via `with` block)
```

### Raw passthrough
| Method | Description |
|---|---|
| `m.send(cmd: str) -> str` | Send any ASCII command, return reply. Raises `DmxError` on `?...`. |
| `m.query_int(cmd: str) -> int` | `int(send(cmd))`. |

---

## Identity

| Attr / method | ASCII | Type |
|---|---|---|
| `m.product_id` | `ID` | `str` (`"DMX-J-SA-USB"`) |
| `m.firmware_version` | `VER` | `str` (`"V307BL"`) |
| `m.device_name` (rw, set with int 0–99) | `DN` / `DN=n` | `str` / `int` |

---

## Motion commands

| Method | ASCII | Notes |
|---|---|---|
| `m.move(value)` | `X<v>` | Move under current mode (ABS/INC). Max delta 262,143. |
| `m.move_absolute(pos)` | `X<v>` | Same wire format; rely on ABS mode being set. |
| `m.set_absolute_mode()` | `ABS` | |
| `m.set_incremental_mode()` | `INC` | |
| `m.move_mode` | `MM` | Returns `MoveMode.ABS` or `MoveMode.INC`. |
| `m.jog_positive()` / `m.jog_negative()` | `J+` / `J-` | Continuous jog. |
| `m.home_positive()` / `m.home_negative()` | `H+` / `H-` | Home input, high speed only. |
| `m.home_hl_positive()` / `m.home_hl_negative()` | `HL+` / `HL-` | High + low speed homing, uses `HCA`. |
| `m.limit_home_positive()` / `m.limit_home_negative()` | `L+` / `L-` | Limit-based home, uses `LCA`. |
| `m.stop()` | `STOP` | Stop with deceleration. |
| `m.abort()` | `ABORT` | Immediate stop. |
| `m.clear_error()` | `CLR` | Clear limit error. |

Position is reset to 0 after `H+/H-/HL+/HL-`. Limit-home (`L+/L-`) returns to position 0 via `LCA`.

---

## Speed and acceleration

| Attr (rw) | ASCII | Range |
|---|---|---|
| `m.high_speed` | `HSPD` | 100–200,000 pps |
| `m.low_speed` | `LSPD` | 100–200,000 pps |
| `m.acceleration` | `ACC` | 10–1,000 ms |

Pulse rate to RPS: `pps = rps * 53.33` (1.8° motor, 16 microstep).

---

## Position and status

| Attr / method | ASCII | Type |
|---|---|---|
| `m.position` (rw) | `PX` / `PX=v` | `int` (32-bit signed) |
| `m.status` | `MST` | `MotorStatus` flags |
| `m.is_moving()` | derived | `bool` |
| `m.wait_until_idle(poll_s=0.02, timeout_s=None)` | polls `MST` | raises `DmxError` on timeout |

### `MotorStatus` (IntFlag)
| Flag | Bit | Meaning |
|---|---|---|
| `CONST_SPEED` | 0 | running at constant speed |
| `ACCEL` | 1 | accelerating |
| `DECEL` | 2 | decelerating |
| `HOME_INPUT` | 3 | home switch active |
| `MINUS_LIMIT_INPUT` | 4 | −limit switch active |
| `PLUS_LIMIT_INPUT` | 5 | +limit switch active |
| `MINUS_LIMIT_ERROR` | 6 | −limit hit during − motion (latched, needs `clear_error()`) |
| `PLUS_LIMIT_ERROR` | 7 | +limit hit during + motion (latched, needs `clear_error()`) |
| `COMM_TIMEOUT_ALARM` | 10 | watchdog tripped |

---

## Current control

| Attr (rw unless noted) | ASCII | Range / units |
|---|---|---|
| `m.run_current` | `CUR` | 100–2,000 mA |
| `m.idle_current` | `ACR` | 0 or 100–2,000 mA (0 = disable on idle) |
| `m.actual_current` (ro) | `CCR` | mA |
| `m.idle_time` | `ICN` | 1–100 centiseconds before dropping to idle |

---

## Enable / digital I/O

| Attr / method | ASCII |
|---|---|
| `m.enable(True/False)` | `EO=1` / `EO=0` |
| `m.enabled` (ro) | `EO` |
| `m.eo_boot` (rw) | `EOBOOT` |
| `m.digital_inputs` (ro, int) | `DI` |
| `m.digital_input(i)` (i=1..5) | `DI<i>` |
| `m.digital_outputs` (rw, int) | `DO` / `DO=v` |
| `m.set_digital_output(i, v)` (i=1..2) | `DO<i>=v` |
| `m.get_digital_output(i)` (i=1..2) | `DO<i>` |
| `m.do_boot` (rw) | `DOBOOT` |

### DI bit map
| Bit | Function |
|---|---|
| 0 | DI1 |
| 1 | DI2 |
| 2 | −Limit |
| 3 | Home |
| 4 | +Limit |

DI is active high. DO is active low.

---

## Limits and homing config

| Attr (rw) | ASCII |
|---|---|
| `m.disable_limit` | `DL` (False=enabled, True=disabled, frees DI3/DI5 as GP) |
| `m.home_correction_amount` | `HCA` (0–262,143) |
| `m.limit_correction_amount` | `LCA` (0–262,143) |
| `m.polarity` | `POL` → `PolarityBit` |

### `PolarityBit` (IntFlag)
| Flag | Bit | Inverts |
|---|---|---|
| `DIRECTION` | 0 | direction |
| `LIMIT` | 1 | limit inputs |
| `HOME` | 2 | home input |
| `DIGITAL_OUTPUT` | 3 | DO |
| `DIGITAL_INPUT` | 4 | DI |
| `ENABLE_OUTPUT` | 5 | EO |
| `JUMP_LINE0_ON_ERROR` | 6 | standalone error → line 0 |

---

## Watchdog

| Attr (rw) | ASCII |
|---|---|
| `m.comm_timeout` | `TOC` (ms; 0 disables) |

When triggered, sets `MotorStatus.COMM_TIMEOUT_ALARM`.

---

## Variables

50 user variables, 32-bit signed.

| Method | ASCII |
|---|---|
| `m.get_variable(i)` | `V<i>` |
| `m.set_variable(i, v)` | `V<i>=v` |

V0–V24 reset to 0 on boot. V25–V49 persist via `STORE`.

---

## Standalone programs

Two threads (program 0 / 1). Memory: 1275 lines (~7.5 KB).

| Method | ASCII |
|---|---|
| `m.program_run(p=0)` | `SR<p>=1` |
| `m.program_stop(p=0)` | `SR<p>=0` |
| `m.program_pause(p=0)` | `SR<p>=2` |
| `m.program_continue(p=0)` | `SR<p>=3` |
| `m.program_state(p=0)` | `SASTAT<p>` → `ProgramState` |
| `m.program_counter(p=0)` | `SPC<p>` |
| `m.sload` (rw) | `SLOAD` (bit0=run prog0 on boot, bit1=run prog1 on boot) |
| `m.get_program_line(line)` | `SA<line>` |
| `m.set_program_line(line, val)` | `SA<line>=v` |
| `m.call_subroutine(n)` (n=0..31) | `GS<n>` |

### `ProgramState` (IntEnum)
| Value | Name |
|---|---|
| 0 | `IDLE` |
| 1 | `RUNNING` |
| 2 | `PAUSED` |
| 4 | `ERROR` |

Sub 31 is reserved for error handling — auto-called on standalone error.

---

## Persistence

```python
m.store_to_flash()   # STORE
```

Saved to flash: `DN`, `POL`, `CUR`, `ACR`, `ICN`, `DOBOOT`, `EOBOOT`, `LCA`, `HCA`, `DL`, `SLOAD`, `TOC`, `V25–V49`. Standalone program is auto-stored when downloaded.

---

## Exceptions

| Class | Cause |
|---|---|
| `DmxError` | Device replied `?...` (limit error, overmove, bad command, etc). Raised by `send()`. |
| `PerformaxError` | DLL-level failure: open, close, send/recv, timeouts. |

`DmxError` extends `PerformaxError`.

### Common reply errors
| Reply | Cause |
|---|---|
| `?[Command]` | unknown command |
| `?LimErrored` | motor latched in limit error — call `clear_error()` |
| `?Moving` | move issued while motor still pulsing |
| `?Overmove` | X delta > 262,143 |
| `?State Error` | move while in error state |
| `?Current Range` | current outside 100–2000 mA |
| `?Index out of Range` | bad index for command |
| `?Sub not Initialized` | `GS<n>` to undefined subroutine |

---

## Module: `performax.py`

Low-level ctypes wrap of `PerformaxCom.dll`. Use directly only if you need bypass `DmxJsa`.

```python
PerformaxDLL(dll_path="PerformaxCom.dll")
  .num_devices() -> int
  .product_string(idx, option=0) -> str
  .open(idx) -> int                  # handle
  .close(handle)
  .set_timeouts(read_ms, write_ms)
  .send_recv(handle, command) -> str # 64-byte buffers each way
  .flush(handle)                     # if available in this DLL
```

Loader search order: `./dlls/<name>` → `./<name>` (script dir) → system `PATH`.
