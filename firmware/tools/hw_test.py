# EXSU 620 P1 Drain Optics - hardware bring-up test (MicroPython, Pico 2 W)
# Proves every part is wired right and streams the agreed CSV format.
# Pins and settings match wiring-diagram.png and the hardware interface doc.
import time
from machine import Pin, I2C, PWM
import neopixel

ADDR = 0x29
ATIME = 0xC0          # 64 cycles = 153.6 ms integration
GAIN = 1              # 0=1x 1=4x 2=16x 3=60x; freeze once chosen
GAIN_X = (1, 4, 16, 60)
INT_MS = 154
LIGHT = "pixel"       # "led" = white LED on GP15, "pixel" = NeoPixel 0 as the light source
PIXEL_ON = (60, 60, 60)  # WHITE, so both green and red channels get light (card measures green/red ratio); freeze once chosen

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100_000)
led = Pin(15, Pin.OUT, value=1)       # active low: 0 = LED on
button = Pin(16, Pin.IN, Pin.PULL_UP)  # 0 = pressed
ring = neopixel.NeoPixel(Pin(18), 16)
buzzer = PWM(Pin(20))
buzzer.duty_u16(0)

def wr(reg, val):
    i2c.writeto_mem(ADDR, 0x80 | reg, bytes([val]))

def sensor_init():
    found = i2c.scan()
    if ADDR not in found:
        raise OSError("TCS34725 not found, I2C scan: %s" % found)
    chip = i2c.readfrom_mem(ADDR, 0x80 | 0x12, 1)[0]
    print("# sensor id 0x%02x" % chip)   # 0x44 or 0x4D
    wr(0x01, ATIME)
    wr(0x0F, GAIN)
    wr(0x00, 0x01)                       # power on
    time.sleep_ms(3)
    wr(0x00, 0x03)                       # power on + RGBC enable

def read_crgb():
    d = i2c.readfrom_mem(ADDR, 0xA0 | 0x14, 8)   # auto-increment block read
    c, r, g, b = (d[i] | d[i + 1] << 8 for i in range(0, 8, 2))
    return r, g, b, c

def settle_read():
    time.sleep_ms(INT_MS)    # discard the cycle that straddled the LED switch
    time.sleep_ms(INT_MS)
    return read_crgb()

def light(on):
    if LIGHT == "led":
        led.value(0 if on else 1)
    else:
        ring[0] = PIXEL_ON if on else (0, 0, 0)
        ring.write()

def show(color):
    for i in range(1 if LIGHT == "pixel" else 0, 16):
        ring[i] = color
    ring.write()

def beep(freq=2000, ms=150):
    buzzer.freq(freq)
    buzzer.duty_u16(20000)
    time.sleep_ms(ms)
    buzzer.duty_u16(0)

sensor_init()
for color in ((40, 0, 0), (0, 40, 0), (0, 0, 40), (0, 0, 0)):  # ring self-test, low brightness
    show(color)
    time.sleep_ms(300)
beep()
print("t_ms,r_dark,g_dark,b_dark,c_dark,r_on,g_on,b_on,c_on,gain_x,int_ms,ack")
while True:
    light(False)
    dark = settle_read()
    light(True)
    lit = settle_read()
    light(False)
    ack = 1 if button.value() == 0 else 0
    if ack:
        beep(1000, 80)
    show((0, 30, 0) if lit[3] < 60000 else (30, 0, 0))   # red = saturated, lower GAIN
    print(",".join(str(v) for v in (time.ticks_ms(),) + dark + lit + (GAIN_X[GAIN], INT_MS, ack)))
