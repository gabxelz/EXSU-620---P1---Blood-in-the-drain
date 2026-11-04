# Bill of materials

All parts come from the EXSU 620 Project 01 kit unless noted.

| Qty | Part | Used for |
|---|---|---|
| 1 | Raspberry Pi Pico 2 W (+1 spare) | Microcontroller, MicroPython |
| 1 | Grove Shield for Pi Pico v1.0 | I2C0 port for the sensor, D18 socket for the ring |
| 1 | TCS34725 RGB colour sensor | Measures light through the drain tube (I2C 0x29) |
| 1 | Grove to STEMMA QT / jumper cable | Sensor to Grove I2C0 |
| 1 | White 5 mm LED | Light source in the tube clip |
| 1 | 330 Ω resistor (330–680 Ω OK) | LED current limit, about 3–6 mA |
| 1 | NeoPixel Ring 16 | Alarm light |
| 1 | PAM8302 2.5 W mono amplifier | Drives the speaker from GP20 PWM |
| 1 | 8 Ω speaker | Alarm sound |
| 1 | Pushbutton (panel mount, Ø16 mm) | Acknowledge / silence |
| 1 | Half-size breadboard + male-female jumpers | Wiring |
| 1 | Micro USB cable | Power + serial to laptop |
| 1 | IV giving set (drip chamber, roller clamp, ~4.1 mm OD tubing) + bag | Drain line stand-in |
| 1 | Collection cup | Drain output, timed flow measurement |
| – | Red food colouring / haemoglobin analogue | Blood stand-in for calibration mixes |
| 1 | 0.1 g scale | Making calibration mixes (1 g ≈ 1 mL) |
| 1 | Calipers, multimeter | Measuring tube OD, checking wiring |
| – | PLA filament (black for clip, white/light grey for case) | Printed parts |
| – | Black electrical tape | Light-proofing the clip |

## Printed parts

| Part | File | Size |
|---|---|---|
| Tube clip v4 | cad/tube-clip/DrainOptics_TubeClip_v4.stl | fits 4.1 mm OD tube, 12.2 mm beam |
| Case base | cad/enclosure/T6_caseA_base_v1.stl | 152 × 94 × 50 mm |
| Case lid | cad/enclosure/T6_caseA_lid_v1.stl | 152 × 94 × 6.6 mm |
| Light cap | cad/enclosure/T6_light_cap_v1.stl | 44 × 44 × 15.3 mm |

## Software (all free)

MicroPython for Pico 2 W, Thonny, CadQuery (Python) for the CAD sources, PrusaSlicer or Cura for slicing, Git/GitHub Classroom for submission.
