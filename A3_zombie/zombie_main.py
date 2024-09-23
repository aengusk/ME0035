import time
from Tufts_ble import Sniff, Yell
from machine import Pin, PWM
import neopixel
flag = True
def callback(p):
    global flag
    flag = not flag
p = Pin('GPIO20', Pin.IN, machine.Pin.PULL_UP)  # guess with PULL_UP does...
p.irq(trigger=Pin.IRQ_RISING, handler=callback)
def peripheral():
    p = Yell()
    buzz = PWM(Pin('GPIO18', Pin.OUT))
    buzz.freq(440)
    led = Pin('GPIO0', Pin.OUT)
    neo = neopixel.NeoPixel(Pin(28), 1)
    # neo[0] = (0, 255, 0)
    # neo.write()
    for i in range(10000):
        if flag == True:
            # buzz.duty_u16(1000)
            led.on()
            neo[0] = (200, 0, 255)
            neo.write()
            p.advertise(f'!{i%13 + 1}')
            time.sleep(0.1)
        elif flag == False:
            buzz.duty_u16(0)
            led.off()
            neo[0] = (0, 0, 0)
            neo.write()
            time.sleep(0.1)
            p.stop_advertising()
peripheral()