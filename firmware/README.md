# Firmware (MicroPython, Pico 2 W)

| File | Purpose |
|---|---|
| `main.py` | The monitor. Save to the Pico as `main.py`. Reads sensor 1, converts to % blood and mL/h, drives the ring, speaker and ack button. |
| `tools/sensor1_read.py` | Prints dark/lit counts and the averaged g/r ratio; use for calibration. |
| `tools/hw_test.py` | Bring-up test: checks the sensor, LED, ring, speaker and button. |
| `archive/monitor_2sensor.py` | Earlier design with a second sensor counting drops on the drip chamber. Kept for the design history; not used. |

Setup and settings: see the main [README](../README.md#running-the-firmware).
