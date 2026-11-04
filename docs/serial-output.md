# Serial output (firmware/main.py)

The Pico prints one text line per reading over USB serial (USB CDC, so any baud setting works; about 8 lines per second):

```
BLOOD_PCT:0.85% | EST_RATE:1.5 mL/h (at 180 mL/h flow) | STATE:ADVISORY | SPREAD:0.0123 | SILENCED:False
```

| Field | Meaning |
|---|---|
| `BLOOD_PCT` | % blood from the calibration curve (0 below the 0.3 % noise deadband). |
| `EST_RATE` | Estimated blood loss, mL/h = BLOOD_PCT / 100 × FLOW_MLH. |
| `at ... flow` | The hand-measured drain flow set in `FLOW_MLH`. |
| `STATE` | NORMAL, ADVISORY, CRITICAL, CHECK_DRAIN or AIR_BLANK. CHECK_DRAIN and AIR_BLANK are technical alarms and must never be read as "no bleeding". |
| `SPREAD` | Relative change of the raw green/red ratio over the last 60 s; used to tune `STATIC_BAND`. |
| `SILENCED` | True while the acknowledge button's 2 min silence is active. |

The first line after start-up is a header: `Drain Optics (1 sensor) | baseline g/r 1.3406 | flow set to 180 mL/h`.

Regex to parse a line:

```
BLOOD_PCT:([\d.]+)% \| EST_RATE:([\d.]+) mL/h \(at ([\d.]+) mL/h flow\) \| STATE:(\w+) \| SPREAD:([\d.]+) \| SILENCED:(\w+)
```
