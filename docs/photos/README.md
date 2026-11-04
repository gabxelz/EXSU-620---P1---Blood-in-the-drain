# Build log (photos)

Photos the team took while building the Drain Optics bench prototype, in build order.

| # | Photo | What it shows |
|---|---|---|
| 1 | ![](01-pam8302-amp-parts.jpg) | PAM8302 amplifier as it comes in the kit, with its screw terminal and header pins before soldering. |
| 2 | ![](02-breadboard.jpg) | The half-size breadboard used for power rails, the LED resistor, the button and the amp. |
| 3 | ![](03-first-wiring-led-test.jpg) | First wiring: Pico 2 W on the Grove shield, colour sensor on jumpers, white LED lit for a light test. |
| 4 | ![](04-pico-sensor-ring-wired.jpg) | Pico, colour sensor and NeoPixel ring wired together on the bench. |
| 5 | ![](05-speaker-and-neopixel-ring.jpg) | 8 Ω speaker with its leads, next to the NeoPixel Ring 16 used for the alarm light. |
| 6 | ![](06-amp-on-breadboard.jpg) | PAM8302 amp placed on the breadboard. |
| 7 | ![](07-amp-wired-to-pico.jpg) | Amp wired to the Pico: A+ to GP20, Vin to VBUS, grounds to the rail. |
| 8 | ![](08-ack-button-and-led-wiring.jpg) | Acknowledge button (GP16 to GND) and white LED leads added. |
| 9 | ![](09-soldering-amp-header.jpg) | Fitting the header pins to the amp for soldering. |
| 10 | ![](10-pico-grove-shield-closeup.jpg) | Close-up of the Pico 2 W on the Grove shield with all leads plugged in. |
| 11 | ![](11-parts-in-test-box.jpg) | Everything taped inside a clear test box before the printed case. |
| 12 | ![](12-red-food-colouring.jpg) | Red food colouring used as the blood stand-in for the calibration mixes. |
| 13 | ![](13-final-wiring-powered.jpg) | Final wiring powered over USB in the case. |
| 14 | ![](14-tcs34725-sensor.jpg) | TCS34725 colour sensor with its jumper leads. |
| 15 | ![](15-serial-output-advisory.jpg) | Serial output in Thonny during a bench run: about 1.5 % blood, ADVISORY state, alarm silenced by the button. This run used the team's earlier script, which turns % blood into mL/h with a fixed factor rather than a measured flow. |
| 16 | ![](16-final-rig-critical-red-ring.jpg) | Full bench rig: dyed fluid running through the IV tubing and the printed tube clip (right), electronics in the printed case, NeoPixel ring red for CRITICAL. |
| 17 | ![](17-dashboard-blood-loss-chart.jpg) | Software group's dashboard (`localhost:5000`): live blood-loss chart in mL/h, blood concentration (1.91 %) and alarm-silence status. |
| 18 | ![](18-telegram-critical-alert.jpg) | Notification path: the DrainOptics Telegram bot sends a CRITICAL alert (103.7 mL/h, 1.87 % blood) to a registered phone. |

## Videos

- [`../videos/demo-device-normal-to-advisory.mp4`](../videos/demo-device-normal-to-advisory.mp4) (56 s): the monitor script running in Thonny, the sensor clip on the tubing, and the output moving from NORMAL to ADVISORY with the ring and speaker responding. Audio is filtered so only the alarm beeps remain (from about 0:30).
- [`../videos/demo-dashboard-live.mp4`](../videos/demo-dashboard-live.mp4) (17 s): the live dashboard on the laptop updating as the fluid in the tube changes.
