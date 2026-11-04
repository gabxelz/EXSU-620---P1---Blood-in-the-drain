# Drain Optics: optical blood-loss monitor for surgical drain output

EXSU 620 Digital Prototyping, Project 01 (Group 1). Bench prototype.

After surgery, nurses judge bleeding from a drain by eye and write down a colour word. Drain Optics clips a colour sensor onto the drain tubing, measures how red the fluid is, converts that to **% blood** with a calibration curve, and estimates the **blood loss rate in mL/h**. A second sensor on the drip chamber watches for drops and raises a **BLOCKED** alarm when they stop. A NeoPixel ring and a speaker raise alarms, a button silences them, and the software subgroup's **web dashboard** and **Telegram channel** show the readings and send CRITICAL alerts by text.

> **Bench prototype only.** Dyed water stands in for blood. The alarm limits are bench demo values with no clinical basis. Not for use on patients.

## Repository layout

| Folder | Contents |
|---|---|
| [`firmware/`](firmware/) | MicroPython for the Raspberry Pi Pico 2 W. `main.py` is the final two-sensor monitor. |
| [`firmware/tools/`](firmware/tools/) | Calibration helper, drop-counter test, pin finder, wiring bring-up test. |
| [`firmware/archive/`](firmware/archive/) | Earlier versions: one-sensor monitor, and the two-sensor version that used drop counting for flow. |
| [`cad/tube-clip/`](cad/tube-clip/) | Tube clip v4 (holds the sensor and white LED around the drain tube): STL, STEP, CadQuery source. |
| [`cad/enclosure/`](cad/enclosure/) | Electronics case v3: base, snap lid, light cap (STL + STEP), assembly STEP, CadQuery source. |
| [`docs/`](docs/) | Wiring diagrams, case pictures, serial data format ([`docs/serial-output.md`](docs/serial-output.md)). |
| [`docs/photos/`](docs/photos/) | Build log: photos of the prototype being built and tested. |
| [`docs/videos/`](docs/videos/) | Demo videos: device alarm states and the live dashboard. |
| [`report/`](report/) | Design dossier (D9, PDF), filled group report, failure modes list. |
| [`software/`](software/) | Software subgroup: web dashboard and Telegram alerts. |
| [`BOM.md`](BOM.md) | Bill of materials. |

## How it works

1. A white LED shines through the drain tube in the printed clip. A TCS34725 colour sensor on the other side reads red, green, blue and clear light.
2. Blood absorbs green light much more than red, so the **green/red ratio** falls as the fluid gets bloodier.
3. Absorbance `A = 1 − (g/r) / BASE_RATIO`, where `BASE_RATIO` is the clear-water g/r (1.3406 in our clip).
4. A four-point calibration curve converts A to % blood:

   | Absorbance A | 0.00 | 0.64 | 0.78 | 0.86 |
   |---|---|---|---|---|
   | % blood | 0 | 0.5 | 1.0 | 2.0 |

5. **Blood loss rate (mL/h) = % blood / 100 × drain flow (mL/h), calculated from sensor 1.** The drain flow `FLOW_MLH` is measured by hand (timed cup: our calibration run collected 15.7 mL in 10 s = 5652 mL/h; at that flow 1.77 % blood = 100 mL/h, the CRITICAL limit) and typed into `main.py`, so the rate is an estimate, not a measured flow rate.
6. **Sensor 2** is taped to the IV drip chamber with its own LED on and counts drops (light change > 1.8 %). We first planned to measure flow from the drop rate, but on the bench sensor 2 **misses some drops**, so it is used only to detect a **blocked line**: no drop for 10 s = BLOCKED.
7. Alarm states drive the light ring and speaker (see below), and the readings go over USB to the laptop dashboard and Telegram.

## Hardware

Full parts list in [BOM.md](BOM.md). Wiring picture: [`docs/images/full-wiring.png`](docs/images/full-wiring.png). Sensor 2 is now wired with 4 jumpers as in the table below (the picture shows an older Grove option for it).

### Pin map (final, two sensors)

| Part | Connection |
|---|---|
| TCS34725 colour sensor (sensor 1, tube clip) | Grove I2C0: SDA GP8, SCL GP9, VIN 3V3, GND. Sensor's own LED pin → GND (onboard LED off). Address 0x29. |
| TCS34725 colour sensor (sensor 2, drip chamber) | 4 jumpers: SDA → GP6 (pin 9), SCL → GP7 (pin 10), **VIN** → 3V3 OUT (pin 36), GND → GND (pin 8). LED and INT pins left open (its LED stays on). Software I2C at 100 kHz. Address 0x29. |
| White LED (in the clip's light hole) | VBUS 5 V → 330 Ω → LED long leg (+); LED short leg (−) → GP15. GP15 LOW = LED on. |
| NeoPixel Ring 16 | Data In → GP18 (Grove D18), 5 V and GND from the same socket. |
| PAM8302 amplifier + 8 Ω speaker | A+ → GP20 (PWM tone), A− → GND, Vin → VBUS, SD left open. Speaker on the screw terminal. |
| Acknowledge button | GP16 ↔ GND (internal pull-up, 0 = pressed). |
| Power + data | Micro USB to the laptop. Grove shield switch set to 3V3. |

### Printed parts

| Part | File | Notes |
|---|---|---|
| Tube clip v4 | `cad/tube-clip/DrainOptics_TubeClip_v4.stl` | Black PLA (or wrap in black tape: white PLA leaks light). Sized for 4.1 mm OD IV tubing; measure yours and edit `tube_od` in `tube_clip_v4_cad.py`. |
| Case base | `cad/enclosure/T6_caseA_base_v1.stl` | 152 × 94 × 50 mm. Front panel holds the button (Ø16.2) and speaker grille. |
| Case lid | `cad/enclosure/T6_caseA_lid_v1.stl` | Snap fit, NeoPixel ring holder, light window. File is already upside down for printing. |
| Light cap | `cad/enclosure/T6_light_cap_v1.stl` | 44 × 44 × 15.3 mm. Translucent / white PLA, diffuses the ring. |

All print with no supports. To regenerate the models: `pip install cadquery`, then run `python tube_clip_v4_cad.py` or `python enclosure_v3_cad.py` in that folder.

### Build photos

See the [build log](docs/photos/README.md) for photos of each build step.

![Full rig in CRITICAL](docs/photos/16-final-rig-critical-red-ring.jpg)

## Demo

| | |
|---|---|
| Live dashboard (software group) | ![Dashboard](docs/photos/17-dashboard-blood-loss-chart.jpg) |
| Telegram CRITICAL alert | ![Telegram alert](docs/photos/18-telegram-critical-alert.jpg) |

Videos: [device going NORMAL → ADVISORY](docs/videos/demo-device-normal-to-advisory.mp4) (56 s) and [live dashboard](docs/videos/demo-dashboard-live.mp4) (17 s). On GitHub, click a video and then **View raw** to play it.

### Fluid rig

Dyed-water IV bag hung ~50 cm up → drip chamber → roller clamp → tubing through the tube clip → collection cup. Make calibration mixes by weight on the 0.1 g scale (1 g ≈ 1 mL). The scale is not used during a logging run.

## Running the firmware

1. Flash **MicroPython** for the Raspberry Pi Pico 2 W (hold BOOTSEL, plug in USB, drag the `.uf2` from micropython.org onto the drive).
2. Open **Thonny**, choose the MicroPython (Raspberry Pi Pico) interpreter.
3. (Optional) Run `firmware/tools/hw_test.py` to check the wiring, and `firmware/tools/drops_per_second.py` to position sensor 2 on the drip chamber (aim at the drip tip; black tape against room light).
4. Measure the drain flow (collect in a cup for a timed period, mL × 3600 ÷ seconds; ours: 15.7 mL in 10 s = 5652) and set `FLOW_MLH` at the top of `firmware/main.py`.
5. Save `firmware/main.py` to the Pico as `main.py`. It starts on power-up. The `neopixel` module is built into MicroPython.
6. Watch the output in Thonny's shell. One line per second:

   ```
   BLOOD_PCT:0.85% | EST_RATE:48.0 mL/h | STATE:ADVISORY | RAW_GR:0.3512 | CLEAR:850 | DROPS/S:1 | TOTAL_DROPS:37 | SILENCED:False
   ```

### Settings (top of `main.py`)

| Setting | Default | Meaning |
|---|---|---|
| `FLOW_MLH` | 5652.0 | Measured drain flow, mL/h. Re-measure if the clamp moves. |
| `ADVISORY_PCT` | 0.5 | % blood for the amber alarm. |
| `CRITICAL_PCT` | 1.77 | % blood for the red alarm (= 100 mL/h at 5652 mL/h flow). |
| `HYST_PCT` | 0.1 | Hysteresis before stepping back down. |
| `NO_DROP_S` | 10 s | No drop seen by sensor 2 for this long = BLOCKED. Set it a little longer than the normal gap between drops. |
| `DROP_THRESHOLD_PCT` | 1.8 % | Light change on sensor 2 that counts as a drop. Lower if drops are missed; raise if it counts with the clamp closed. |
| `STATIC_MS` / `STATIC_BAND` | 60 s / 0.2 % | Sensor 1 reading frozen this long = CHECK DRAIN. |
| `SILENCE_MS` | 120 s | How long the button silences the sound. |
| `VOLUME` | 100 | Speaker PWM duty (0–65535). |

### Alarm states

| State | Ring | Sound | Trigger |
|---|---|---|---|
| NORMAL | green, filled in proportion to % blood | silent | below advisory |
| ADVISORY | amber / yellow | slow beep, 500 Hz | % blood ≥ 0.5 |
| CRITICAL | red | fast beeps, 1 kHz | % blood ≥ 1.77 (= 100 mL/h) |
| **BLOCKED** | **blue, full ring** | **continuous beeping, 880 Hz** | sensor 2 has seen no drop for 10 s (blocked or clamped line, empty bag). Lasts until drops return, then the ring goes back to sensor 1's colour. Never reported as "no bleeding". |
| CHECK_DRAIN | cyan, full ring | long beep every 2 s | sensor 1 reading has not moved for 60 s |
| AIR_BLANK | dim blue, full ring | long beep every 2 s | almost no light reaches sensor 1 (empty tube or unplugged sensor) |

Pressing the button silences the sound for 2 minutes; the light stays on. The sound returns early if the alarm becomes new or worse (including a new BLOCKED alarm).

The dashboard and Telegram alerts are described in [`software/README.md`](software/README.md).

### Calibration

1. Fill the tube with clear water, run `firmware/tools/sensor1_read.py`, and record the averaged g/r ratio as `BASE_RATIO`.
2. Run each mix (0.5 %, 1 %, 2 % blood analogue) through the tube, wait for 10 lines, and record the averaged ratio.
3. Compute `A = 1 − ratio / BASE_RATIO` for each and update `CAL_POINTS` in `main.py`.

Measured on our rig (2026-11-02): useful range is below about 1 % blood; above that the curve flattens.

## Known limitations

These are reported in full in the design dossier (D7 verification report and D9 traceability matrix):

- Flow is entered by hand (timed cup), not measured live, so the mL/h figure is an estimate.
- Sensor 2 misses some drops (it sees reflected light from its own LED, and small drops barely change it), so drop counting was **not accurate enough for flow** and is used only for the BLOCKED alarm. A missed drop can delay the alarm clearing; a run of missed drops longer than 10 s can give a false BLOCKED.
- Alarms are on % blood, not on the mL/h rate, and the "rate doubles within 30 min" rule (CR-2) is not on the device.
- No fouled-window, lamp-failure or saturation check in the final firmware.
- The web dashboard and Telegram channel were built and demonstrated by the software subgroup (see the Demo section); their source code goes in [`software/`](software/).
- Firmware is MicroPython, not the CircuitPython named on the project card.
- An air-filled (empty) tube reads the same as clear water (A = 0.00, 0 % blood) and is not flagged unless almost no light reaches the sensor (AIR_BLANK).
- Bench only: dyed water does not scatter light like real drain fluid.

## Team

EXSU 620 Project 01, Group 1: calibration, software and hardware subgroups. Course lead: Dr. Hooshair.

## License

MIT, see [LICENSE](LICENSE).
