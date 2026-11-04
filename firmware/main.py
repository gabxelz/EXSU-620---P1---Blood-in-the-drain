# Drain Optics monitor, ONE sensor (MicroPython, Pico 2 W). Save to the Pico as main.py so it runs at power-up.
# The team's calibrated monitor, plus:
#   - an honest rate: blood loss rate = % blood / 100 x FLOW_MLH, where FLOW_MLH is the
#     drain flow you MEASURE (time a cup) and type in. One colour sensor cannot measure flow.
#   - a "CHECK DRAIN" alarm: if the reading has not moved at all for 60 s the line may be
#     blocked (a flowing line always flickers a little). Tune STATIC_BAND on the bench.
#   - silence auto-resets after 2 min.
# Sensor settings and calibration points are the team's, unchanged.
import time
from machine import Pin, I2C, PWM
import neopixel

# ---- settings ----
VOLUME = 100              # sound volume (0-65535)
SILENCE_MS = 120_000      # button silences the sound for 2 min
FLOW_MLH = 180.0          # drain flow in mL/h: collect for 5 min, mL x 12. Re-measure if the clamp moves.
ADVISORY_PCT = 0.5        # % blood for amber (team's 0.5 % cup)
CRITICAL_PCT = 1.8        # % blood for red (team's old 100 mL/h point)
HYST_PCT = 0.1            # must fall this far below a limit to step back down
STATIC_MS = 60_000        # reading frozen this long = CHECK DRAIN
STATIC_BAND = 0.002       # "frozen" = g/r moved less than 0.2 % in that time (tune: see SPREAD in the output)

# ---- hardware (as the team's script) ----
i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100_000)
ring = neopixel.NeoPixel(Pin(18), 16)
spk = PWM(Pin(20)); spk.freq(500); spk.duty_u16(0)
btn = Pin(16, Pin.IN, Pin.PULL_UP)
white_led = Pin(15, Pin.OUT, value=0)   # white LED in the tube clip: GP15 LOW = ON (VBUS -> 330 ohm -> LED -> GP15)
ADDR = 0x29
def wr(r, v): i2c.writeto_mem(ADDR, 0x80 | r, bytes([v]))
wr(0x01, 0xD5); wr(0x0F, 0x00); wr(0x00, 0x01); time.sleep_ms(3); wr(0x00, 0x03)
time.sleep_ms(200)

# ---- team calibration (unchanged) ----
BASE_RATIO = 1.3406
CAL_POINTS = [(0.00, 0.0), (0.64, 0.5), (0.78, 1.0), (0.86, 2.0)]

def absorbance_to_pct_blood(a):
    if a <= CAL_POINTS[0][0]:
        return CAL_POINTS[0][1]
    if a >= CAL_POINTS[-1][0]:
        (x0, y0), (x1, y1) = CAL_POINTS[-2], CAL_POINTS[-1]
        return y1 + (a - x1) * (y1 - y0) / (x1 - x0)
    for i in range(len(CAL_POINTS) - 1):
        x0, y0 = CAL_POINTS[i]
        x1, y1 = CAL_POINTS[i + 1]
        if x0 <= a <= x1:
            return y0 + (a - x0) * (y1 - y0) / (x1 - x0)
    return 0.0

# ---- alarm sound ----
state = "NORMAL"
silenced = False
silenced_at = 0
tone = 500
duty = 0

def alarm_tick():
    global tone, duty, silenced, silenced_at
    t = time.ticks_ms()
    if btn.value() == 0 and state != "NORMAL" and not silenced:
        silenced, silenced_at = True, t
    if silenced and time.ticks_diff(t, silenced_at) > SILENCE_MS:
        silenced = False
    if state == "ADVISORY":                     on, f = t % 1000 < 300, 500   # slow beep
    elif state == "CRITICAL":                   on, f = t % 300 < 150, 1000   # fast beeps
    elif state in ("CHECK_DRAIN", "AIR_BLANK"): on, f = t % 2000 < 600, 750   # long beep every 2 s
    else:                                       on, f = False, 500
    if f != tone:
        spk.freq(f); tone = f
    want = VOLUME if on and not silenced else 0
    if want != duty:
        spk.duty_u16(want); duty = want

def wait(ms):
    end = time.ticks_add(time.ticks_ms(), ms)
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        alarm_tick()
        time.sleep_ms(5)

def get_gr_ratio():
    wait(110)
    d = i2c.readfrom_mem(ADDR, 0xB4, 8)
    c, r, g, b = (d[i] | d[i + 1] << 8 for i in range(0, 8, 2))
    return g / max(r, 1), c

ratio_history = []
static_log = []          # (time, raw g/r) over the last STATIC_MS
started = time.ticks_ms()
COLOURS = {"NORMAL": (0, 20, 0), "ADVISORY": (25, 12, 0), "CRITICAL": (30, 0, 0),
           "CHECK_DRAIN": (0, 15, 15), "AIR_BLANK": (0, 0, 10)}

print("Drain Optics (1 sensor) | baseline g/r %.4f | flow set to %.0f mL/h" % (BASE_RATIO, FLOW_MLH))
try:
    while True:
        raw_ratio, clear_raw = get_gr_ratio()
        t = time.ticks_ms()
        ratio_history.append(raw_ratio)
        ratio_history = ratio_history[-5:]
        curr_ratio = sum(ratio_history) / len(ratio_history)

        # frozen-reading check on the RAW ratio (a flowing line always flickers a little)
        static_log.append((t, raw_ratio))
        while time.ticks_diff(t, static_log[0][0]) > STATIC_MS:
            static_log.pop(0)
        vals = [v for _, v in static_log]
        spread = (max(vals) - min(vals)) / max(curr_ratio, 1e-6)
        frozen = time.ticks_diff(t, started) > STATIC_MS and spread < STATIC_BAND

        pct_blood = 0.0
        ml_per_hour = 0.0
        if clear_raw < 10:
            new_state = "AIR_BLANK"            # empty tube or sensor unplugged
        elif frozen:
            new_state = "CHECK_DRAIN"          # possibly blocked: nurse should check the line
        else:
            a = max(0.0, 1.0 - curr_ratio / BASE_RATIO)
            pct_blood = absorbance_to_pct_blood(a)
            if pct_blood < 0.3:
                pct_blood = 0.0                # team's noise deadband
            ml_per_hour = pct_blood / 100.0 * FLOW_MLH
            s = state if state in ("NORMAL", "ADVISORY", "CRITICAL") else "NORMAL"
            if s == "NORMAL":
                new_state = "ADVISORY" if pct_blood >= ADVISORY_PCT else "NORMAL"
            elif s == "ADVISORY":
                if pct_blood >= CRITICAL_PCT:                   new_state = "CRITICAL"
                elif pct_blood < ADVISORY_PCT - HYST_PCT:       new_state = "NORMAL"
                else:                                           new_state = "ADVISORY"
            else:
                new_state = "ADVISORY" if pct_blood < CRITICAL_PCT - HYST_PCT else "CRITICAL"

        if new_state == "NORMAL" or (new_state != state and new_state != "ADVISORY"):
            silenced = False                   # a new or worse alarm always sounds again
        state = new_state

        col = COLOURS.get(state, (0, 20, 0))
        n = 16 if state in ("CHECK_DRAIN", "AIR_BLANK") else max(1, min(16, round(pct_blood / CRITICAL_PCT * 16)))
        for i in range(16):
            ring[i] = col if i < n else (0, 0, 0)
        ring.write()

        print("BLOOD_PCT:%.2f%% | EST_RATE:%.1f mL/h (at %.0f mL/h flow) | STATE:%s | SPREAD:%.4f | SILENCED:%s"
              % (pct_blood, ml_per_hour, FLOW_MLH, state, spread, silenced))
finally:
    spk.duty_u16(0)
    for i in range(16): ring[i] = (0, 0, 0)
    ring.write()
