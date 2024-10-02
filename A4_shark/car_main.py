import time
import network
from mqtt import MQTTClient
import secrets
import asyncio
from machine import Pin, PWM, reset
import neopixel
from random import random

# The threadsleep config controls the 'await asyncio.sleep(threadsleep)' statement
# that appears once in each thread's while True loop to yield processor time to the other processes.
threadsleep = 0.01

class WheelController:
    def __init__(self):
        self.throttle = 0.0
        self.angle = 0.0
        self.side = 'left' # pressing the button switches from left to right
        self.button = Pin('GPIO20', Pin.IN, Pin.PULL_UP)

        self.pwm_LF = PWM(Pin(27))
        self.pwm_LF.freq(20000)
        self.pwm_LF.duty_u16(0) # can be any positive integer 0-1023

        self.pwm_LB = PWM(Pin(26))
        self.pwm_LB.freq(20000)
        self.pwm_LB.duty_u16(0) # can be any positive integer 0-1023

        self.pwm_RF = PWM(Pin(19))
        self.pwm_RF.freq(20000)
        self.pwm_RF.duty_u16(0) # can be any positive integer 0-1023

        self.pwm_RB = PWM(Pin(21))
        self.pwm_RB.freq(20000)
        self.pwm_RB.duty_u16(0) # can be any positive integer 0-1023

        # 1 degrees is just to the right of straight
        # 359 degrees is just to the left of straight


        self.neopixel = neopixel.NeoPixel(Pin(28), 1)  # NeoPixel on GPIO 28
        self.neopixel[0] = (10, 0, 0); self.neopixel.write() # the neopixel should be red for the left controller and green for the right controller
        
        self.connect_to_wifi()


    def connect_to_wifi(self):
        self.neopixel[0] = (10, 0, 10); self.neopixel.write()
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(secrets.ssid, secrets.password)
        
        print('trying to connect to Wi-Fi', end = '')
        while self.wlan.ifconfig()[0] == '0.0.0.0':
            print('.', end='')
            time.sleep(1)

        # We should have a valid IP now via DHCP
        print('\nWi-Fi connection successful: {}'.format(self.wlan.ifconfig()))
        self.neopixel[0] = (10, 0, 0); self.neopixel.write()

    async def test(self):
        testiter = 0
        while True: # change to self.is_human
            testiter += 1
            await asyncio.sleep(1)
            print(testiter)
            await asyncio.sleep(threadsleep)

    async def monitor_mqtt(self):
        mqtt_broker = 'broker.hivemq.com' 
        port = 1883
        topic = 'ME35-24/Rex'

        def callback(topic, msg):
            topic, msg = topic.decode(), msg.decode()
            print('received message {}'.format(msg))

            try: 
                msg = eval(msg)
            except NameError:
                pass
            print('the message was of type {}'.format(type(msg)))
            if isinstance(msg, float) or isinstance(msg, int):
                self.angle = float(msg)
                print('set angle to {}'.format(float(msg)))
            elif isinstance(msg, tuple) and len(msg) == 2:
                #self.drive_motors(*msg)
                if msg[0] > msg[1]:
                    self.throttle = 1.0
                else:
                    self.throttle = 0.0

            elif isinstance(msg, str):
                if msg == 'forward':
                    self.throttle = 1.0
                    print('set throttle to 1')
                elif msg == 'backward':
                    self.throttle = -1.0
                    print('set throttle to -1')
                elif msg == 'stop':
                    self.throttle = 0.0
                    print('set throttle to 0')
                else: 
                    print("the message was an unknown string {}".format(msg))
        client = MQTTClient('ME35_aengus', mqtt_broker, port, keepalive=60)
        client.set_callback(callback)
        client.connect()
        client.subscribe(topic.encode())

        while True:
            try:
                client.check_msg()
            except OSError:
                print('OSError WAS RAISED')
                self.neopixel[0] = (10, 10, 0); self.neopixel.write()
                reset()
                # recall self.connect_to_wifi here?
            await asyncio.sleep(threadsleep)
    
    async def monitor_button(self):
        while True:
            if self.button.value() == 0: # the button is pressed:
                if self.side == 'left':
                    self.side = 'right'
                    self.neopixel[0] = (0, 10, 0); self.neopixel.write()
                elif self.side == 'right':
                    # switch the side to 'left' and the neopixel to red
                    self.side = 'left'
                    self.neopixel[0] = (10, 0, 0); self.neopixel.write()
                else:
                    raise RuntimeError("self.side was {} instead of 'left' or 'right'".format(self.side))
            await asyncio.sleep(threadsleep)

    # def transform(self, x, range1, range2):
    #     a, b = range1
    #     c, d = range2
    #     return (d-c)/(b-a) * (x-a) + c
    
    def drive_motors(self, left, right): # where each is a float between -1.0 and 1.0
        print('about to drive motors with {}, {}'.format(left, right))
        assert isinstance(left, float) or isinstance(left, int)
        assert isinstance(right, float) or isinstance(right, int)
        if left < -1:
            left = -1
        if left > 1:
            left = 1
        if right < -1:
            right = -1
        if right > 1:
            right = 1
        if left == 0: # stop both left ones 
            self.pwm_LF.duty_u16(0)
            self.pwm_LB.duty_u16(0)
        elif left > 0: # left forward
            self.pwm_LF.duty_u16(int(65535 * left))
            self.pwm_LB.duty_u16(0)
        elif left < 0: # left backward
            self.pwm_LF.duty_u16(0)
            self.pwm_LB.duty_u16(int(-65535 * left))
        if right == 0: # stop both right ones
            self.pwm_RF.duty_u16(0)
            self.pwm_RB.duty_u16(0)
        elif right > 0: # right forward
            self.pwm_RF.duty_u16(int(65535 * right))
            self.pwm_RB.duty_u16(0)
        elif right < 0: # right backward
            self.pwm_RF.duty_u16(0)
            self.pwm_RB.duty_u16(int(-65535 * right))

    def left_right_from_self(self):
        if self.angle == 0:
            return self.throttle, self.throttle
        if 0< self.angle < 180: 
            return self.throttle, self.throttle*(1-self.angle/45)
        if 180 < self.angle:
            return self.throttle*((self.angle-315)/45), self.throttle
        raise AssertionError('l_r_f_s final block flow reach error')

    # def return_motor_speeds_from_data(self):
    #     if self.throttle == 0:
    #         return (0,0)
    #     elif self.throttle > 0:
    #         if 180 < self.angle: # turning left
    #             return (self.transform(self.angle, (180, 270), (1, -1)), 1)
    #         elif self.angle <= 180: # turning right
    #             return (1, self.transform(self.angle, (90, 180), (-1, 1)))
    #     elif self.throttle < 0:
    #         if 180 < self.angle: # turning left
    #             return (self.transform(self.angle, (180, 270), (-1, 1)), -1)
    #         elif self.angle <= 180: # turning right
    #             return (-1, self.transform(self.angle, (90, 180), (1, -1)))
            
    # def control_motors_from_motor_speeds(self, data_pair):
    #     if data_pair == (0, 0):
    #         self.pwm_forward.duty_u16(0)
    #         self.pwm_backward.duty_u16(0)
    #     else:
    #         if self.side == 'left':
    #             velocity = data_pair[0]
    #         elif self.side == 'right':
    #             velocity = data_pair[1]
    #         else:
    #             raise RuntimeError("self.side was {} instead of 'left' or 'right'".format(self.side))
    #         pwm_duty = int(abs(self.transform(velocity, (0, 1), (0, 1023))))
    #         if velocity > 0:
    #             self.pwm_forward.duty_u16(0)
    #             self.pwm_backward.duty_u16(0)
    #         else:
    #             self.pwm_forward.duty_u16(0)
    #             self.pwm_backward.duty_u16(0)

    # def left_motor_from_angle(angle):
    #     return angle + angle
    
    # def right_motor_from_angle(angle):
    #     return angle + angle


    async def control_motor(self, test = False):
        while True:
            left, right = self.left_right_from_self()
            if test:
                print('testing self.drive_motors({}, {})'.format(left, right))
            else:
                print(' reallyself.drive_motors({}, {})'.format(left, right))
                self.drive_motors(left, right)
            await asyncio.sleep(threadsleep)

async def main():
    wc = WheelController()
    await asyncio.gather(asyncio.create_task(wc.monitor_mqtt()),
                         asyncio.create_task(wc.test()),
                         asyncio.create_task(wc.monitor_button()), 
                         asyncio.create_task(wc.control_motor(test = False))
                        )

asyncio.run(main())