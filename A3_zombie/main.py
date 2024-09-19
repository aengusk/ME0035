import ssd1306
from machine import Pin, I2C
import Tufts_ble
import asyncio
import time # time.ticks_ms() returns the number of miliseconds since the device powered on
from aable import Sniff

threadsleep = 0.1 # await asyncio.sleep(threadsleep)

class Human:
    def __init__(self):
        self.i2c = I2C(1, scl=Pin(27), sda=Pin(26), freq=400000)
        self.oled = ssd1306.SSD1306_I2C(128, 64, self.i2c)

        self.data_line_template = {'is connected': False,       # whether we are connected to this zombie right now
                                   'connected since': None,     # the timestamp (using time.ticks_ms()) when we connected
                                   'connected for': None,       # how long since the timstamp when we connected
                                   'times infected': 0}         # how many times we've been infected by them (3 secs -> 1 infection)

        self.data = {i: dict(self.data_line_template) for i in range(1, 15)}

        self.sniffer = Sniff('!', verbose = False)

        self.led = Pin('GPIO0', Pin.OUT)

    async def control_led(self):
        while True:
            if True in [self.data[zombie_number]['is connected'] for zombie_number in self.data.keys()]:
                self.led.on()
            else:
                self.led.off()
            await asyncio.sleep(threadsleep)

    async def monitor_bluetooth(self):
        self.sniffer.scan(0)
        while True:
            message, rssi = self.sniffer.last, self.sniffer.rssi
            if message:
                print(rssi)
                zombie_number = int(message[1:])
                threshold = -60
                if rssi > threshold:
                    self.data[zombie_number]['is connected'] = True
                    #print(self.data[zombie_number])
                else:
                    self.data[zombie_number]['is connected'] = False
                self.sniffer.last = self.sniffer.rssi = None
            else:
                pass
                # for i in range(1, 14):
                #     self.data[i]['is connected'] = False
            await asyncio.sleep(threadsleep)

    async def print_connections(self):
        while True:
            print('is connected: ', self.data[9]['is connected'])
            await asyncio.sleep(threadsleep)

    async def test(self):
        testiter = 0
        while True:
            testiter += 1
            await asyncio.sleep(1)
            print(testiter)
            await asyncio.sleep(threadsleep)




# human.sniffer.scan(0)

# while True:
#     message, rssi = human.sniffer.last, human.sniffer.rssi
#     if message:
#         print(message)
#         print(rssi)
#         human.sniffer.last = human.sniffer.rssi = None
#     time.sleep(0.1)   

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

    async def update_screen(self):
        while True:
            self.display_data()
            await asyncio.sleep(threadsleep)

async def main():    
    human = Human()
    task1 = asyncio.create_task(human.monitor_bluetooth())
    task2 =  asyncio.create_task(human.update_screen())
    task3 =  asyncio.create_task(human.test())
    task4 =  asyncio.create_task(human.control_led())
    await asyncio.gather(task1, task2, task3, task4)

asyncio.run(main())