"""Continuous jog. Ctrl+C to stop cleanly."""
import time
from dmx_j_sa import DmxJsa, MotorStatus


def main():
    with DmxJsa.open_first() as m:
        m.enable(True)
        m.high_speed = 5000     # pps
        m.low_speed = 500
        m.acceleration = 300    # ms
        m.run_current = 1000    # mA

        print(f"jogging at {m.high_speed} pps. Ctrl+C to stop.")
        m.jog_positive()        # use jog_negative() for opposite dir

        try:
            while True:
                if m.status & (MotorStatus.PLUS_LIMIT_ERROR | MotorStatus.MINUS_LIMIT_ERROR):
                    print("limit hit, clearing"); m.clear_error(); break
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nstopping...")
        finally:
            m.stop()
            m.wait_until_idle(timeout_s=5)
            m.enable(False)
            print(f"final position: {m.position}")


if __name__ == "__main__":
    main()
