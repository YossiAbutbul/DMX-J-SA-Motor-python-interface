# DMX-J-SA Python Interface

Python wrapper for **Arcus DMX-J-SA** integrated NEMA 17 step motor + driver + controller (USB 2.0). Implements every interactive ASCII command from §10 of Manual rev 1.10 (compatible with firmware V307BL).

## Requirements

- Windows (DLL is Windows-only)
- Python 3.8+ (32-bit OR 64-bit — bundled DLLs are x64; for 32-bit Python, replace with x86 build)
- External **+12 to +24 VDC** on V+ pin. USB alone won't power the motor windings — comms will work but motor won't move.

## Repo layout

```
.
├── dmx_j_sa.py        # high-level DmxJsa class
├── performax.py       # ctypes wrapper of PerformaxCom.dll
├── example.py         # smoke test (1 rev)
├── dlls/              # bundled x64 driver DLLs (auto-loaded)
│   ├── PerformaxCom.dll
│   └── SiUSBXp.dll
└── docs/
    └── API.md         # full Python API reference
```

`performax.py` searches `./dlls/` first, then the script directory, then `PATH`.

## Quick start

```python
from dmx_j_sa import DmxJsa

with DmxJsa.open_first() as m:
    m.enable(True)
    m.high_speed = 5000      # pps (100..200000)
    m.low_speed = 500
    m.acceleration = 300     # ms (10..1000)
    m.run_current = 1000     # mA (100..2000)
    m.set_incremental_mode()
    m.move(3200)             # 1 rev (16 microstep, 1.8°)
    m.wait_until_idle()
    print(m.position)
```

## API summary

Full reference: [docs/API.md](docs/API.md).

### Connection
| Python | Notes |
|---|---|
| `DmxJsa.list_devices()` | List Performax USB device strings |
| `DmxJsa.open_first()` | Open device 0, returns context manager |
| `DmxJsa(device_index=0)` | Open by index |
| `m.close()` | Release handle |
| `m.send(cmd)` / `m.query_int(cmd)` | Raw ASCII passthrough |

### Identity
| Python | ASCII | Returns |
|---|---|---|
| `m.product_id` | `ID` | `"DMX-J-SA-USB"` |
| `m.firmware_version` | `VER` | e.g. `"V307BL"` |
| `m.device_name` / `m.device_name = n` | `DN` / `DN=n` | `"JSA00"`–`"JSA99"` |

### Motion
| Python | ASCII |
|---|---|
| `m.move(v)` / `m.move_absolute(v)` | `X<v>` |
| `m.set_absolute_mode()` / `m.set_incremental_mode()` | `ABS` / `INC` |
| `m.move_mode` | `MM` → `MoveMode` |
| `m.jog_positive()` / `m.jog_negative()` | `J+` / `J-` |
| `m.home_positive()` / `m.home_negative()` | `H+` / `H-` |
| `m.home_hl_positive()` / `m.home_hl_negative()` | `HL+` / `HL-` |
| `m.limit_home_positive()` / `m.limit_home_negative()` | `L+` / `L-` |
| `m.stop()` (decel) / `m.abort()` (immediate) | `STOP` / `ABORT` |
| `m.clear_error()` | `CLR` |

Max delta on `X` move: **262,143** pulses.

### Speed & accel
| Python | ASCII | Range |
|---|---|---|
| `m.high_speed` | `HSPD` | 100..200,000 pps |
| `m.low_speed` | `LSPD` | 100..200,000 pps |
| `m.acceleration` | `ACC` | 10..1,000 ms |

### Position & status
| Python | ASCII |
|---|---|
| `m.position` / `m.position = v` | `PX` / `PX=v` |
| `m.status` | `MST` → `MotorStatus` flags |
| `m.is_moving()` | derived from `MST` |
| `m.wait_until_idle(poll_s, timeout_s)` | polls `MST` |

`MotorStatus` bits: `CONST_SPEED`, `ACCEL`, `DECEL`, `HOME_INPUT`, `MINUS_LIMIT_INPUT`, `PLUS_LIMIT_INPUT`, `MINUS_LIMIT_ERROR`, `PLUS_LIMIT_ERROR`, `COMM_TIMEOUT_ALARM`.

### Current control
| Python | ASCII | Range |
|---|---|---|
| `m.run_current` | `CUR` | 100..2,000 mA |
| `m.idle_current` | `ACR` | 0 or 100..2,000 mA |
| `m.actual_current` | `CCR` | read-only |
| `m.idle_time` | `ICN` | 1..100 cs |

### Enable / digital I/O
| Python | ASCII |
|---|---|
| `m.enable(True/False)` / `m.enabled` | `EO=1`/`EO=0` / `EO` |
| `m.eo_boot` | `EOBOOT` |
| `m.digital_inputs` (5-bit) | `DI` |
| `m.digital_input(i)` (i=1..5) | `DI<i>` |
| `m.digital_outputs` (2-bit) | `DO` / `DO=v` |
| `m.set_digital_output(i, v)` / `m.get_digital_output(i)` | `DO<i>=v` / `DO<i>` |
| `m.do_boot` | `DOBOOT` |

DI map: bit0=DI1, bit1=DI2, bit2=−Limit, bit3=Home, bit4=+Limit.

### Limits & homing config
| Python | ASCII |
|---|---|
| `m.disable_limit` | `DL` |
| `m.home_correction_amount` | `HCA` |
| `m.limit_correction_amount` | `LCA` |
| `m.polarity` | `POL` → `PolarityBit` |

### Watchdog
| Python | ASCII |
|---|---|
| `m.comm_timeout` (ms, 0 disables) | `TOC` |

### Variables (V0..V49)
| Python | ASCII |
|---|---|
| `m.get_variable(i)` | `V<i>` |
| `m.set_variable(i, v)` | `V<i>=v` |

### Standalone programs
| Python | ASCII |
|---|---|
| `m.program_run(p)` / `program_stop(p)` / `program_pause(p)` / `program_continue(p)` | `SR<p>=1/0/2/3` |
| `m.program_state(p)` | `SASTAT<p>` → `ProgramState` |
| `m.program_counter(p)` | `SPC<p>` |
| `m.sload` | `SLOAD` |
| `m.get_program_line(line)` / `m.set_program_line(line, val)` | `SA<line>` / `SA<line>=v` |
| `m.call_subroutine(n)` (n=0..31) | `GS<n>` |

`p` is 0 or 1 (two threads). Lines are 0..1274 (~7.5 KB).

### Persistence
| Python | ASCII |
|---|---|
| `m.store_to_flash()` | `STORE` |

Persisted: `DN`, `POL`, `CUR`, `ACR`, `ICN`, `DOBOOT`, `EOBOOT`, `LCA`, `HCA`, `DL`, `SLOAD`, `TOC`, `V25..V49`. (Standalone program is auto-stored on download.)

## Errors

`DmxError` is raised when the device replies with `?...`:

| Reply | Cause |
|---|---|
| `?[Command]` | unknown command |
| `?LimErrored` | motor in limit error |
| `?Moving` | move/position cmd while pulsing |
| `?Overmove` | X delta > 262,143 |
| `?State Error` | move while in error state |
| `?Current Range` | current outside 100..2000 mA |
| `?Index out of Range` | bad index |
| `?Sub not Initialized` | `GS<n>` to undefined sub |

`PerformaxError` covers DLL-level failures (open, send, etc).

## Hardware notes

- Pulse/rev = 3200 (1.8° motor × 16 microstep). RPS × 53.33 = pps.
- Power input 12–24 VDC on V+ pin — **required for motor motion**, not just USB.
- Limits/Home are opto-isolated NPN, sink to opto-ground to activate.
- Outputs are opto-isolated open-collector PNP (active low), need external current-limiting resistor, max 45 mA.
