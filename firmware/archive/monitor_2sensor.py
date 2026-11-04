# Drain Optics monitor, TWO sensors (MicroPython, Pico 2 W)
# Sensor 1 (tube clip, I2C0 GP8/GP9): colour -> % blood, team calibration unchanged.
# Sensor 2 (drip chamber, SoftI2C GP6 SDA / GP7 SCL, its LED left ON): counts drops -> drain flow.
#   flow mL/h       = drops per minute x 60 / DROP_FACTOR
#   blood loss mL/h = % blood / 100 x flow mL/h
# CHECK DRAIN alarm: no drop for 10 s while running = line blocked, clamp shut or bag empty.
# If sensor 2 is not found the script still runs, using FLOW_MLH and the "frozen reading" check.
# Silence button: 2 min, then auto-reset; a new or worse alarm sounds again at once.
import time
from machine import Pin, I2C, SoftI2C, PWM
import neopixel

# ---- settings ----
VOLUME = 100              # sound volume (0-65535)
SILENCE_MS = 120_000      # button silences the sound for 2 min
DROP_FACTOR = 20          # drops per mL. ASSUMED (standard adult IV set); not printed on our packet
FLOW_MLH = 180.0          # fallback flow, only used if sensor 2 is missing
ADVISORY_PCT = 0.5        # % blood for amber (team's 0.5 % cup)
CRITICAL_PCT = 1.8        # % blood for red (team's old 100 mL/h point)
HYST_PCT = 0.1            # must fall this far below a limit to step back down
STATIC_MS = 10_000        # no drop for 10 s = CHECK DRAIN (blue ring). Needs more than 6 drops/min or it false-alarms
STATIC_BAND = 0.002       # fallback only: "frozen" colour reading
# drop detection (same as drip_test.py)
DROP_THRESHOLD = 0.04     # a drop = clear reading moves 4 % from baseline
LOCKOUT_MS = 150          # ignore the rest of the same drop
FLOW_WINDOW_MS = 60_000   # flow = drops in the last 60 s

# ---- hardware (as the team's script) ----
i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100_000)
ring = neopixel.NeoPixel(Pin(18), 16)
spk = PWM(Pin(20)); spk.freq(500); spk.duty_u16(0)
btn = Pin(16, Pin.IN, Pin.PULL_UP)
white_led = Pin(15, Pin.OUT, value=0)   # white LED in the tube clip: GP15 LOW = ON (VBUS -> resistor -> LED -> GP15)
ADDR = 0x29
def wr(r, v): i2c.writeto_mem(ADDR, 0x80 | r, bytes([v]))
wr(0x01, 0xD5); wr(0x0F, 0x00); wr(0x00, 0x01); time.sleep_ms(3); wr(0x00, 0x03)
time.sleep_ms(200)

# ---- sensor 2: drop counter ----
di2c = SoftI2C(sda=Pin(6), scl=Pin(7), freq=400_000)
def dwr(r, v): di2c.writeto_mem(ADDR, 0x80 | r, bytes([v]))
def read_drip():
    d = di2c.readfrom_mem(ADDR, 0xA0 | 0x14, 2)
    return d[0] | d[1] << 8
drip_ok = False
try:
    if ADDR in di2c.scan():
        dwr(0x01, 0xFF); dwr(0x0F, 0x01); dwr(0x00, 0x01); time.sleep_ms(3); dwr(0x00, 0x03)
        time.sleep_ms(50)
        drip_ok = True
except OSError:
    pass
drip_base = read_drip() if drip_ok else 0
drop_times = []           # tick of each drop in the last FLOW_WINDOW_MS
drops_total = 0
last_drop = time.ticks_ms()

def drip_tick():
    global drip_base, last_drop, drops_total
    if not drip_ok:
        return
    try:
        c = read_drip()
    except OSError:
        return
    now = time.ticks_ms()
    if drip_base and abs(c - drip_base) / drip_base > DROP_THRESHOLD:
        if time.ticks_diff(now, last_drop) > LOCKOUT_MS:
            last_drop = now
            drops_total += 1
            drop_times.append(now)
    else:
        drip_base += (c - drip_base) / 50     # slow baseline follows room light

def flow_mlh(now):
    while drop_times and time.ticks_diff(now, drop_times[0]) > FLOW_WINDOW_MS:
        drop_times.pop(0)
    span = min(FLOW_WINDOW_MS, max(time.ticks_diff(now, started), 10_000))   # at least 10 s so the first drops do not look huge
    dpm = len(drop_times) * 60_000 / span
    return dpm, dpm * 60 / DROP_FACTOR

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
    elif state == "CHECK_DRAIN":                                                # blocked: beep-beep ... beep ... beep-beep ... beep
        p = t % 2400
        on, f = p < 150 or 250 <= p < 400 or 1200 <= p < 1350, 750
    elif state == "AIR_BLANK":                  on, f = t % 2000 < 600, 750   # long beep every 2 s
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
        drip_tick()               # poll the drop sensor every ~3 ms while sensor 1 integrates
        time.sleep_ms(3)

def get_gr_ratio():
    wait(110)
    d = i2c.readfrom_mem(ADDR, 0xB4, 8)
    c, r, g, b = (d[i] | d[i + 1] << 8 for i in range(0, 8, 2))
    return g / max(r, 1), c

ratio_history = []
static_log = []          # (time, raw g/r) over the last STATIC_MS
started = time.ticks_ms()
COLOURS = {"NORMAL": (0, 20, 0), "ADVISORY": (25, 12, 0), "CRITICAL": (30, 0, 0),
           "CHECK_DRAIN": (0, 0, 30), "AIR_BLANK": (12, 0, 12)}   # blue = no drops for 10 s, purple = sensor 1 sees no light

if drip_ok:
    print("Drain Optics (2 sensors) | baseline g/r %.4f | drop factor %d drops/mL (assumed)" % (BASE_RATIO, DROP_FACTOR))
else:
    print("WARNING: sensor 2 (drops) not found on GP6/GP7 - using fixed flow %.0f mL/h" % FLOW_MLH)
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
        running = time.ticks_diff(t, started) > STATIC_MS
        if drip_ok:
            dpm, flow = flow_mlh(t)
            frozen = running and time.ticks_diff(t, last_drop) > STATIC_MS   # no drop for 60 s
        else:
            dpm, flow = 0.0, FLOW_MLH
            frozen = running and spread < STATIC_BAND

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
            ml_per_hour = pct_blood / 100.0 * flow
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

        print("BLOOD_PCT:%.2f%% | DROPS/S:%.2f | DROPS/MIN:%.0f | FLOW:%.1f mL/h | BLOOD_RATE:%.2f mL/h | STATE:%s | DROPS:%d | SILENCED:%s"
              % (pct_blood, dpm / 60, dpm, flow, ml_per_hour, state, drops_total, silenced))
finally:
    spk.duty_u16(0)
    for i in range(16): ring[i] = (0, 0, 0)
    ring.write()
