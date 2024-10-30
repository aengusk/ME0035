# Python
import time
import asyncio
from math import pi, sin
# MicroPython
from machine import Pin # type: ignore (suppresses Pylance lint warning)
from servo import Servo # type: ignore (suppresses Pylance lint warning)

threadsleep = 0.01

class Dancer:
    def __init__(self):
        self.servo = Servo(2)
        self.happy = True
        self.enabled = True
        self.button = Pin(9, Pin.IN, Pin.PULL_UP)

    async def test(self):
        while True:
            await asyncio.sleep(threadsleep)

    async def monitor_buttons_and_pot(self):
        while True:
            if not self.button.value():
                self.happy = not self.happy
                print(f'self.happy is now {self.happy}')
                await asyncio.sleep(0.5)
            await asyncio.sleep(threadsleep)

    async def run_servos(self):
        frequency = 1 # cycle per second
        # time.ticks_ms() / 1000
        while True:
            if self.enabled:
                if self.happy:
                    frequency = 1.0
                else:
                    frequency = 0.25
                ω = 2*pi*frequency
                t = time.ticks_ms() / 1000
                servo_angle = (sin(ω*t) + 1) / 2 * 90
                self.servo.write(servo_angle)
            await asyncio.sleep(threadsleep)

async def main():
    dancer = Dancer()
    await asyncio.gather(asyncio.create_task(dancer.test()), 
                         asyncio.create_task(dancer.monitor_buttons_and_pot()), 
                         asyncio.create_task(dancer.run_servos())
                        )

asyncio.run(main())