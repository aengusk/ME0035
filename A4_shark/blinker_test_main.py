# Python
import time
# MicroPython
from machine import Pin # type: ignore (suppresses Pylance lint warning)
import neopixel         # type: ignore (suppresses Pylance lint warning)

myneopixel = neopixel.NeoPixel(Pin(28), 1)
while True:
    myneopixel[0] = (10, 10, 10); myneopixel.write()
    time.sleep(1)
    myneopixel[0] = (0, 0, 10); myneopixel.write()
    time.sleep(1)