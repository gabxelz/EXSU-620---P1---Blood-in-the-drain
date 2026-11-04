# EXSU 620 P1 Drain Optics - sensor 1 (tube clip) reading + calibration helper (MicroPython, Pico 2 W)
# Wiring: sensor 1 SDA->GP8, SCL->GP9, VIN->3V3, GND->GND, sensor LED pin->GND (onboard LED OFF).
#         White LED: VBUS -> 330 ohm -> LED long leg, LED short leg -> GP15 (GP15 low = LED on).
# Run in Thonny. Every ~0.7 s it prints one line: dark, lit, net red/green and the green/red ratio.
# For calibration: put one sample in the tube, wait for 10 lines, write down the "avg10" ratio.
import time
from machine import Pin, I2C

ADDR = 0x29
ATIME = 0xC0          # 64 cycles = 154 ms integration
INT_MS = 154
GAIN = 1              # 0=1x 1=4x 2=16x 3=60x. Lower it if you see SATURATED, raise it if you see TOO DARK
GAIN_X = (1, 4, 16, 60)

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100_000)
led = Pin(15, Pin.OUT, value=1)       # 1 = white LED off, 0 = on


def wr(reg, val):
    i2c.writeto_mem(ADDR, 0x80 | reg, bytes([val]))


def read_rgbc():
    d = i2c.readfrom_mem(ADDR, 0xA0 | 0x14, 8)
    c, r, g, b = (d[i] | d[i + 1] << 8 for i in range(0, 8, 2))
    return r, g, b, c


def settle_read():
    time.sleep_ms(2 * INT_MS + 5)     # skip the reading that overlapped the LED switching
    return read_rgbc()


if ADDR not in i2c.scan():
    raise OSError("Sensor 1 not found on GP8/GP9. Check SDA/SCL are not swapped and VIN is on 3V3.")
wr(0x01, ATIME)
wr(0x0F, GAIN)
wr(0x00, 0x01)
time.sleep_ms(3)
wr(0x00, 0x03)

print("# gain %dx, integration %d ms" % (GAIN_X[GAIN], INT_MS))
print("dark_r,dark_g,lit_r,lit_g,net_r,net_g,ratio_g_r,avg10,status")
hist = []
while True:
    led.value(1)
    dark = settle_read()
    led.value(0)
    lit = settle_read()
    led.value(1)
    net_r = lit[0] - dark[0]
    net_g = lit[1] - dark[1]
    if max(lit) >= 60000:
        status = "SATURATED: lower GAIN"
    elif lit[3] - dark[3] < 200:
        status = "TOO DARK: LED off/misaimed, or raise GAIN"
    elif dark[3] > 0.2 * lit[3]:
        status = "ROOM LIGHT LEAK: tape the clip"
    else:
        status = "ok"
    ratio = net_g / net_r if net_r > 0 else 0
    hist.append(ratio)
    hist = hist[-10:]
    avg = sum(hist) / len(hist)
    print("%d,%d,%d,%d,%d,%d,%.4f,%.4f,%s" % (dark[0], dark[1], lit[0], lit[1], net_r, net_g, ratio, avg, status))
