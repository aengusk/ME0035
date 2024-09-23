import ssd1306
from machine import Pin, I2C
import Tufts_ble
import asyncio
import time # time.ticks_ms() returns the number of miliseconds since the device powered on
from aable import Sniff
import neopixel

threadsleep = 0.001 # await asyncio.sleep(threadsleep)

class Human:
    def __init__(self):
        self.rssi_threshold = -60 # bluetooth yells must be greater than this number to count
        self.forget_threshold = 0.5 # the number of seconds until we call it a new encounter

        self.is_human = True

        self.i2c = I2C(1, scl=Pin(27), sda=Pin(26), freq=400000)
        self.oled = ssd1306.SSD1306_I2C(128, 64, self.i2c)

        self.data_line_template = {'state': 0,                      # this comes from the state machine, see hard copy of explanation
                                   'is connected': False,           # whether we are connected to this zombie right now
                                   'connected since': None,         # the timestamp (using time.ticks_ms()) when we first
                                   'last connected': None,          # the timestamp (using time.ticks_ms()) when we last connected
                                   'connected for': None,           # how long since the timstamp when we connected
                                   'just got us': False,            # whether this encounter has already been counted as an infection
                                   'times infected': 0}             # how many times we've been infected by them (3 secs -> 1 infection)

        self.data = {i: dict(self.data_line_template) for i in range(1, 15)}

        self.sniffer = Sniff('!', verbose = False)

        self.led = Pin('GPIO0', Pin.OUT)
        self.all_leds = tuple(Pin('GPIO' + str(i), Pin.OUT) for i in range(6))
        self.neopixel = neopixel.NeoPixel(Pin(28), 1)  # NeoPixel on GPIO 28

    async def test(self):
        testiter = 0
        while True: # change to self.is_human
            testiter += 1
            await asyncio.sleep(1)
            print(testiter)
            await asyncio.sleep(threadsleep)

    async def monitor_bluetooth(self):
        '''
        This function monitors the Bluetooth channels for messages in the form '!4'
        Its only output is to modify self.data[z]['last connected']
        self.update_data will keep track of the other points in self.data
        '''
        self.sniffer.scan(0)
        while self.is_human:
            message, rssi = self.sniffer.last, self.sniffer.rssi
            if message:
                print(rssi)
                zombie_number = int(message[1:])
                if rssi > self.rssi_threshold:
                    self.data[zombie_number]['last connected'] = time.ticks_ms()/1000
                    #print(self.data[zombie_number])
                # else:
                #     self.data[zombie_number]['is connected'] = False
                self.sniffer.last = self.sniffer.rssi = None
            # else:
            #     for i in range(1, 14):
            #         self.data[i]['is connected'] = False
            await asyncio.sleep(threadsleep)

    async def update_data(self):
        '''
        All we have from self.monitor_bluetooth is 
        self.data[z]['last connected'] for each zombie_number
        '''
        while self.is_human:
            for z in self.data.keys(): # where z is the zombie number
                if self.data[z]['state'] == 0:
                    if self.data[z]['last connected']:
                        self.data[z]['state'] = 1
                        self.data[z]['connected since'] = self.data[z]['last connected']
                        self.data[z]['is connected'] = True
                        self.data[z]['connected for'] = 0.0
                elif self.data[z]['state'] == 1:
                    self.data[z]['connected for'] = self.data[z]['last connected'] - self.data[z]['connected since']
                    if time.ticks_ms()/1000 - self.data[z]['last connected'] > self.forget_threshold:
                        self.data[z]['state'] = 0
                        self.data[z]['connected since'] = None
                        self.data[z]['is connected'] = False
                        self.data[z]['last connected'] = None
                        self.data[z]['connected for'] = None
                    elif self.data[z]['connected for'] > 3.0:
                        self.data[z]['state'] = 2
                        self.data[z]['just got us'] = True
                        self.data[z]['times infected'] += 1
                        if self.data[z]['times infected'] >= 3:
                            self.become_zombie()
                elif self.data[z]['state'] == 2:
                    # self.data[z]['connected for'] = self.data[z]['last connected'] - self.data[z]['connected since'] # I think this is not necessary
                    if time.ticks_ms()/1000 - self.data[z]['last connected'] > self.forget_threshold:
                        self.data[z]['state'] = 0
                        self.data[z]['connected since'] = None
                        self.data[z]['is connected'] = False
                        self.data[z]['last connected'] = None
                        self.data[z]['connected for'] = None
                        self.data[z]['just got us'] = False
                await asyncio.sleep(threadsleep) # notice this is inside of both the while and the for

    async def print_connections(self):
        while self.is_human:
            print('is connected: ', self.data[9]['is connected'])
            await asyncio.sleep(threadsleep)

    def data_line_as_string(self, line_number):
        to_return = '' # start with an empty string and gradually append data to it
        if line_number == 8 or line_number == 9:
            to_return += ' '
        to_return += str(line_number)
        to_return += '!' if self.data[line_number]['is connected'] else ' '
        #to_return += str(self.data[line_number]['connected for']) if self.data[line_number]['is connected'] else '   '
        to_return += 'X' if self.data[line_number]['times infected'] >= 1 else ' '
        to_return += 'X' if self.data[line_number]['times infected'] >= 2 else ' '
        to_return += 'X' if self.data[line_number]['times infected'] >= 3 else ' '
        #print(to_return + 'EOL')
        return to_return

    def display_data(self):
        self.oled.fill(0)
        self.oled.text(self.data_line_as_string( 1) + self.data_line_as_string( 8), 0, 0)
        self.oled.text(self.data_line_as_string( 2) + self.data_line_as_string( 9), 0, 8)
        self.oled.text(self.data_line_as_string( 3) + self.data_line_as_string(10), 0,16)
        self.oled.text(self.data_line_as_string( 4) + self.data_line_as_string(11), 0,24)
        self.oled.text(self.data_line_as_string( 5) + self.data_line_as_string(12), 0,32)
        self.oled.text(self.data_line_as_string( 6) + self.data_line_as_string(13), 0,40)
        self.oled.text(self.data_line_as_string( 7) + self.data_line_as_string(14), 0,48)
        self.oled.show()

    async def control_screen(self):
        while self.is_human:
            self.display_data()
            await asyncio.sleep(threadsleep)

    async def control_led(self):
        while self.is_human:
            if True in [self.data[zombie_number]['is connected'] for zombie_number in self.data.keys()]:
                self.led.on()
            else:
                self.led.off()
            await asyncio.sleep(threadsleep)

    def become_zombie(self):
        self.is_human = False
        ## more tk, start broadcasting bluetooth

async def main():    
    human = Human()
    test = asyncio.create_task(human.test())
    monitor_bluetooth = asyncio.create_task(human.monitor_bluetooth())
    update_data =  asyncio.create_task(human.update_data())
    print_connections =  asyncio.create_task(human.print_connections())
    control_screen =  asyncio.create_task(human.control_screen())
    control_led = asyncio.create_task(human.control_led())
    await asyncio.gather(test, 
                         monitor_bluetooth, 
                         update_data, 
                         print_connections, 
                         control_screen, 
                         control_led)

asyncio.run(main())