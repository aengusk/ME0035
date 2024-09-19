import ssd1306
from machine import Pin, I2C
import Tufts_ble
import asyncio
import time # time.ticks_ms() returns the number of miliseconds since the device powered on

class Human:
    def __init__(self):
        self.i2c = I2C(1, scl=Pin(27), sda=Pin(26), freq=400000)
        self.oled = ssd1306.SSD1306_I2C(128, 64, self.i2c)

        self.data_line_template = {'is connected': False,       # whether we are connected to this zombie right now
                                   'connected since': None,     # the timestamp (using time.ticks_ms()) when we connected
                                   'connected for': None,       # how long since the timstamp when we connected
                                   'times infected': 0}         # how many times we've been infected by them (3 secs -> 1 infection)

        self.data = {i: dict(self.data_line_template) for i in range(1, 15)}

    def data_line_as_string(self, line_number):
        to_return = '' # start with an empty string and gradually append data to it
        if line_number == 8 or line_number == 9:
            to_return += ' '
        to_return += str(line_number)
        # to_return += '!' if self.data[line_number]['is connected'] else ' '
        to_return += str(self.data[line_number]['connected for']) if self.data[line_number]['is connected'] else '   '
        to_return += 'X' if self.data[line_number]['times infected'] >= 1 else ' '
        to_return += 'X' if self.data[line_number]['times infected'] >= 2 else ' '
        to_return += 'X' if self.data[line_number]['times infected'] >= 3 else ' '
        
        print(to_return + 'EOL')

        return to_return
    
    def test_add_data_randomly(self):
        self.data[4]['is connected'] = True
        self.data[4]['times infected'] = 2
        self.data[4]['connected since'] = time.ticks_ms() # not important
        self.data[4]['connected for'] = 1.3

        self.data[10]['is connected'] = True
        self.data[10]['times infected'] = 3
        self.data[10]['connected since'] = time.ticks_ms() # not important
        self.data[10]['connected for'] = 2.0

    def test_screen(self):
        self.oled.fill(0)
        self.oled.text('QMMMMMMMMMMMMMM_', 0, 0)
        self.oled.text('QMMMMMMMMMMMMMM_', 0, 8)
        self.oled.text('QMMMMMMMMMMMMMM_', 0, 16)
        self.oled.text('QMMMMMMMMMMMMMM_', 0, 24)
        self.oled.text('QMMMMMMMMMMMMMM_', 0, 32)
        self.oled.text('QMMMMMMMMMMMMMM_', 0, 40)
        self.oled.text('QMMMMMMMMMMMMMM_', 0, 48)
        self.oled.text('BMMMMMMMMMMMMMM_', 0, 56)
        self.oled.show()
    
    def test_screen_2(self):
        self.oled.fill(0)
        self.oled.text('1234567890\n12345678901234567890', 0, 0)
        self.oled.show()

    def test_screen_3(self):
        self.oled.fill(0)
        self.oled.text('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n', 0, 0)
        self.oled.text('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n', 0, 8)
        self.oled.text('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n', 0, 16)
        self.oled.text('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n', 0, 24)
        self.oled.text('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n', 0, 32)
        self.oled.text('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n', 0, 40)
        self.oled.text('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n', 0, 48)
        self.oled.text('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n', 0, 56)
        self.oled.show()

    def print_data(self):
        print(self.data)

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


human = Human()

if True:
    human.test_add_data_randomly()
    human.display_data()
    print(100)

while True: 
    import time
from hub import port
import motor, motor_pair
from Tufts_ble import Sniff, Yell

def car():
    motor_pair.unpair(motor_pair.PAIR_1)  # unpair an older pairing if it exists
    motor_pair.pair(motor_pair.PAIR_1, port.E, port.F)
    
    c = Sniff('!', verbose = False)
    c.scan(0)   # 0ms = scans forever 
    while True:
        if c.last:
            steering = int(c.last[1:])
            print(steering)
            motor_pair.move(motor_pair.PAIR_1, steering, velocity=280, acceleration=100) #0 is steering - go straight (-100 to 100)   
        time.sleep(0.1)
    motor_pair.stop(motor_pair.PAIR_1)
    motor_pair.unpair(motor_pair.PAIR_1)  
    time.sleep(1)