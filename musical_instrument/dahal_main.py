# Python
import time
import asyncio
from math import pi, sin
# MicroPython
from machine import Pin, I2C    # type: ignore (suppresses Pylance lint warning)
import network                  # type: ignore (suppresses Pylance lint warning)
from servo import Servo         # type: ignore (suppresses Pylance lint warning)
# custom
from mqtt import MQTTClient     # type: ignore (suppresses Pylance lint warning)
import ssd1306                  # type: ignore (suppresses Pylance lint warning)
import secrets

threadsleep = 0.01

class Dancer:
    def __init__(self):
        self.servo = Servo(2)
        self.happy = True
        self.enabled = True
        self.button = Pin(9, Pin.IN, Pin.PULL_UP)

        self.i2c = I2C(0, scl=Pin(7), sda=Pin(6), freq=400000)
        self.oled = ssd1306.SSD1306_I2C(128, 64, self.i2c)

        self.connect_to_wifi()

    def connect_to_wifi(self):
        #self.neopixel[0] = (10, 0, 10); self.neopixel.write()
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(secrets.ssid, secrets.password)
        
        print('trying to connect to Wi-Fi', end = '')
        while self.wlan.ifconfig()[0] == '0.0.0.0':
            print('.', end='')
            time.sleep(1)

        # We should have a valid IP now via DHCP
        print('\nWi-Fi connection successful: {}'.format(self.wlan.ifconfig()))
        #self.neopixel[0] = (10, 0, 0); self.neopixel.write()

    def write_to_screen(self, text):
        self.oled.text(text, 0, 0)
        self.oled.show()

    async def test(self):
        testiter = 0
        while True:
            testiter += 1
            await asyncio.sleep(1)
            print(testiter)
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

    async def monitor_mqtt(self):
        mqtt_broker = 'broker.hivemq.com' # old
        # mqtt_broker = 'broker.emqx.io' # new
        port = 1883
        topic = 'ME35-24/aengus'

        def callback(topic, msg):
            topic, msg = topic.decode(), msg.decode()
            print('received MQTT message {}'.format(msg))
            if msg == 'happy':
                self.happy = True
            elif msg == 'sad':
                self.happy = False
            elif msg == 'enable':
                self.enabled = True
            elif msg == 'disable':
                self.enabled = False
                print('disabled myself')
        print('about to attempt MQTT connection')
        
        self.client = MQTTClient('ME35_aengus', mqtt_broker, port, keepalive=60)
        self.client.set_callback(callback)
        self.client.connect()
        self.client.subscribe(topic.encode())

        print('successfully connected to MQTT')

        while True:
            self.client.check_msg()
            await asyncio.sleep(threadsleep)

async def main():
    dancer = Dancer()
    dancer.write_to_screen('aengus')
    await asyncio.gather(asyncio.create_task(dancer.test()), 
                         asyncio.create_task(dancer.monitor_buttons_and_pot()), 
                         asyncio.create_task(dancer.monitor_mqtt()), 
                         asyncio.create_task(dancer.run_servos())
                        )

asyncio.run(main())