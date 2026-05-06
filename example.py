"""Smoke test: rotate motor 1 revolution."""
from dmx_j_sa import DmxJsa


def main():
    with DmxJsa.open_first() as m:
        print(f"{m.product_id} fw={m.firmware_version} name={m.device_name}")

        m.enable(True)
        m.high_speed = 5000
        m.low_speed = 500
        m.acceleration = 300
        m.run_current = 1000
        m.idle_current = 300

        m.set_incremental_mode()
        m.position = 0
        m.move(3200)            # 1 rev
        m.wait_until_idle(timeout_s=10)
        print(f"position={m.position} status={m.status!r}")

        m.enable(False)


if __name__ == "__main__":
    main()
