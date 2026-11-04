# Drain Optics monitor, TWO sensors (MicroPython, Pico 2 W). Save to the Pico as main.py.
# Final version (4 Nov 2026): main.py merged with the software group's revision
#   (CRITICAL 1.77 % = 100 mL/h, RAW_GR and CLEAR in the serial line, one line per second).
# Sensor 1 (tube clip, GP8/GP9): % blood -> ring colour green / amber / red, as in the 1-sensor monitor.
# Blood loss rate (mL/h) comes from sensor 1: % blood / 100 x FLOW_MLH (drain flow measured by timed cup).
# Sensor 2 (drip chamber, GP6 SDA / GP7 SCL, its own LED on): counts drops. It misses some drops, so it is
#   NOT used for the rate; it is used only to detect a BLOCKED line.
# BLOCKED: no drop seen for NO_DROP_S seconds -> ring turns BLUE and the speaker beeps continuously
#          until drops are seen again; then the ring goes back to showing sensor 1.
import time
from machine import Pin, I2C, SoftI2C, PWM
import neopixel

# ---- settings ----
VOLUME = 100              # sound volume (0-65535)
SILENCE_MS = 120_000      # button silences the sound for 2 min
FLOW_MLH = 5652.0         # drain flow in mL/h: calibration run 15.7 mL in 10 s (x 360). Re-measure if the clamp moves.
ADVISORY_PCT = 0.5        # % blood for amber (team's 0.5 % cup)
CRITICAL_PCT = 1.77       # % blood for red: 1.77 % x 5652 mL/h = 100 mL/h (CR-2 limit)
HYST_PCT = 0.1            # must fall this far below a limit to step back down
STATIC_MS = 60_000        # reading frozen this long = CHECK DRAIN
STATIC_BAND = 0.002       # "frozen" = g/r moved less than 0.2 % in that time (tune: see SPREAD in the output)
# ---- sensor 2: drops ----
NO_DROP_S = 10            # seconds with no drop before the BLOCKED alarm. Your drip is slow (a drop every few s),
                          # so 1 s would alarm all the time. Set it a bit longer than the gap between drops.
DROP_THRESHOLD_PCT = 1.8  # a drop = sensor 2 light changes this much from its baseline
LOCKOUT_MS = 120          # one drop is never counted twice within this time

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

# ---- sensor 2 (drops) ----
di2c = SoftI2C(sda=Pin(6), scl=Pin(7), freq=100_000, timeout=500)
def dwr(r, v): di2c.writeto_mem(ADDR, 0x80 | r, bytes([v]))
def drd():
    d = di2c.readfrom_mem(ADDR, 0xB4, 2)
    return d[0] | d[1] << 8
have_drip = ADDR in di2c.scan()
if have_drip:
    dwr(0x01, 0xFD); dwr(0x0F, 0x02); dwr(0x00, 0x01); time.sleep_ms(3); dwr(0x00, 0x03)   # 7.2 ms, 16x
    time.sleep_ms(20)
    d_base = drd()
d_in = False
d_last = time.ticks_ms()
d_total = 0
d_this_s = 0
d_rate = 0
d_sec = time.ticks_ms()
blocked = False            # True = no drop for NO_DROP_S: blue ring + continuous beeping
PRINT_MS = 1000            # one status line per second (dashboard / logger)
last_print = 0

def drip_tick():
    global d_base, d_in, d_last, d_total, d_this_s, d_rate, d_sec
    if not have_drip:
        return
    now = time.ticks_ms()
    try:
        v = drd()
    except OSError:
        return
    ch = abs(v - d_base) / max(d_base, 1) * 100
    if ch > DROP_THRESHOLD_PCT:
        if not d_in and time.ticks_diff(now, d_last) > LOCKOUT_MS:
            d_total += 1; d_this_s += 1; d_last = now
        d_in = True
        if time.ticks_diff(now, d_last) > 400:     # long change = light level moved, not a drop
            d_base = v; d_in = False
    else:
        d_in = False
        d_base = d_base * 0.98 + v * 0.02
    if time.ticks_diff(now, d_sec) >= 1000:
        d_rate = d_this_s; d_this_s = 0; d_sec = now

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
    if btn.value() == 0 and (state != "NORMAL" or blocked) and not silenced:
        silenced, silenced_at = True, t
    if silenced and time.ticks_diff(t, silenced_at) > SILENCE_MS:
        silenced = False
    if blocked:                                 # BLOCKED: continuous beeping, 880 Hz, 4 beeps per second
        on, f = t % 250 < 150, 880
    elif state == "ADVISORY":                   on, f = t % 1000 < 300, 500   # slow beep
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
        drip_tick()
        time.sleep_ms(3)

def get_gr_ratio():
    wait(110)
    d = i2c.readfrom_mem(ADDR, 0xB4, 8)
    c, r, g, b = (d[i] | d[i + 1] << 8 for i in range(0, 8, 2))
    return g / max(r, 1), c

def report(st, pct, mlh, raw_gr, clear, t):
    # one line per second, fields as the software group's logger expects
    global last_print
    if time.ticks_diff(t, last_print) < PRINT_MS:
        return
    last_print = t
    print("BLOOD_PCT:%.2f%% | EST_RATE:%.1f mL/h | STATE:%s | RAW_GR:%.4f | CLEAR:%d | DROPS/S:%d | TOTAL_DROPS:%d | SILENCED:%s"
          % (pct, mlh, st, raw_gr, clear, d_rate, d_total, silenced))

ratio_history = []
static_log = []          # (time, raw g/r) over the last STATIC_MS
started = time.ticks_ms()
COLOURS = {"NORMAL": (0, 20, 0), "ADVISORY": (25, 12, 0), "CRITICAL": (30, 0, 0),
           "CHECK_DRAIN": (0, 15, 15), "AIR_BLANK": (0, 0, 10)}

print("Drain Optics (2 sensors) | baseline g/r %.4f | flow set to %.0f mL/h | sensor 2 %s"
      % (BASE_RATIO, FLOW_MLH, "found" if have_drip else "NOT FOUND (no drop alerts)"))
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

        # sensor 2: no drop for NO_DROP_S -> BLOCKED (blue + continuous beeping) until drops return
        now = time.ticks_ms()
        was_blocked = blocked
        blocked = have_drip and time.ticks_diff(now, d_last) >= NO_DROP_S * 1000
        if blocked and not was_blocked:
            silenced = False                   # a new BLOCKED alarm always sounds
        if blocked:
            for i in range(16): ring[i] = (0, 0, 30)
            ring.write()
            report("BLOCKED", pct_blood, ml_per_hour, raw_ratio, clear_raw, t)
            continue

        col = COLOURS.get(state, (0, 20, 0))
        n = 16 if state in ("CHECK_DRAIN", "AIR_BLANK") else max(1, min(16, round(pct_blood / CRITICAL_PCT * 16)))
        for i in range(16):
            ring[i] = col if i < n else (0, 0, 0)
        ring.write()

        report(state, pct_blood, ml_per_hour, raw_ratio, clear_raw, t)
finally:
    spk.duty_u16(0)
    for i in range(16): ring[i] = (0, 0, 0)
    ring.write()
