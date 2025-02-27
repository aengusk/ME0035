# Python
import time
import asyncio
# MicroPython
from machine import Pin, ADC, reset # type: ignore (suppresses Pylance lint warning)
import network                      # type: ignore (suppresses Pylance lint warning)
import neopixel                     # type: ignore (suppresses Pylance lint warning)
# custom
from mqtt import MQTTClient         # type: ignore (suppresses Pylance lint warning)
from BLE_CEEO import Yell           # type: ignore (suppresses Pylance lint warning)
import secrets                      # type: ignore (suppresses Pylance lint warning)

NoteOn = 0x90
NoteOff = 0x80
StopNotes = 123
SetInstroment = 0xC0
Reset = 0xFF

threadsleep = 0.01

USE_WIFI = True

volumes = {'off':0, 'pppp':8,'ppp':20,'pp':31,'p':42,'mp':53,
    'mf':64,'f':80,'ff':96,'fff':112,'ffff':127}

chords = {
    'Am': (76,72,69),       'Ab': (75,72,68), 
    'G': (74,71,67),        'Gm': (74,70,67), 
    'F': (72,69,65),        'Fm': (72,68,65), 
    'Em': (71,67,64),       'Eb': (70,67,63), 
    'C': (67,64,60),        'Cm': (67,63,60),

    # This Is Halloween: 
    'F#m': (73,69,66),
    'Fm6': (65,62,60),
    'Dm':  (69,65,62),
    'Cm':  (67,63,60),
    'Abm': (63,59,56)
}
class FT:
    def __init__(self):
        self.enabled = True

        self.neopixel = neopixel.NeoPixel(Pin(28), 1)  # NeoPixel on GPIO 28
        self.neopixel[0] = (127, 127, 127); self.neopixel.write()
        # self.neopixel[0] = (0, 0, 0); self.neopixel.write()
        self.volume = 96

        self.happy = True
        
        self.button = Pin('GPIO20', Pin.IN, Pin.PULL_UP)

        self.photoresistor = ADC(Pin('GPIO27', Pin.PULL_UP))

        self.button0 = Pin('GPIO0', Pin.IN, Pin.PULL_UP)
        self.button1 = Pin('GPIO1', Pin.IN, Pin.PULL_UP)
        self.button2 = Pin('GPIO2', Pin.IN, Pin.PULL_UP)
        self.button3 = Pin('GPIO3', Pin.IN, Pin.PULL_UP)
        self.button4 = Pin('GPIO4', Pin.IN, Pin.PULL_UP)

        if USE_WIFI:
            self.connect_to_wifi()
        
        self.yeller = Yell("AengusFT", verbose = True, type = 'midi')
        self.yeller.connect_up()
        print('just finished connecting up to Bluetooth')

    def connect_to_wifi(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(secrets.ssid, secrets.password)
        
        print('trying to connect to Wi-Fi', end = '')
        while self.wlan.ifconfig()[0] == '0.0.0.0':
            print('.', end='')
            time.sleep(1)

        # We should have a valid IP now via DHCP
        print('\nWi-Fi connection successful: {}'.format(self.wlan.ifconfig()))

    async def test(self):
        testiter = 0
        while True:
            testiter += 1
            await asyncio.sleep(1)
            print(testiter)
            await asyncio.sleep(threadsleep)

    async def monitor_mqtt_button(self):
        while True:
            if not self.button.value():
                if self.enabled:
                    self.enabled = False
                    self.neopixel[0] = (0, 0, 0); self.neopixel.write()
                else:
                    self.enabled = True
                    self.neopixel[0] = (127, 127, 127); self.neopixel.write()
                print(f'self.happy is now {self.happy}')
                await asyncio.sleep(0.5)
            await asyncio.sleep(threadsleep)

    def send_note(self, note, on = True, volume = 96):
        '''
        note: an integer MIDI note according to 
        https://forum.metasystem.io/forum/metagrid-pro/beta/issues/2981-c-2-c-1-midi-notes-lower-keyboard-range-question
        observed behavior: 55 -> G2 so 60 -> C3
        '''
        channel = 0
        #note = 55
        if on:
            cmd = NoteOn
        else:
            cmd = NoteOff

        channel = 0x0F & channel
        timestamp_ms = time.ticks_ms()
        tsM = (timestamp_ms >> 7 & 0b111111) | 0x80
        tsL =  0x80 | (timestamp_ms & 0b1111111)

        c =  cmd | channel
        payload = bytes([tsM,tsL,c,note,volume])
        self.yeller.send(payload)

    async def send_chord(self, chord, volume = 96, duration = 0.5):
        '''
        chord: a str in chords.keys()
        duration: can be None or a time in seconds after which to unpress the notes
        '''
        print('about to press the chord')
        for note in chords[chord]:
            self.send_note(note, on = True, volume = volume)

        
        if duration is not None:
            print('about to unpress the chord')
            await asyncio.sleep(duration)
            for note in chords[chord]:
                self.send_note(note, on = False, volume = volume)


    async def monitor_mqtt(self):
        # mqtt_broker = 'broker.hivemq.com' # old
        mqtt_broker = 'broker.emqx.io' # new
        port = 1883
        topic = 'ME35-24/Team'

        def callback(topic, msg):
            topic, msg = topic.decode(), msg.decode()
            print('received MQTT message {}'.format(msg))
            if msg == 'happy':
                self.happy = True
            elif msg == 'sad':
                self.happy = False
            elif msg == 'enable' or msg == 'on_4':
                self.enabled = True
                self.neopixel[0] = (127, 127, 127); self.neopixel.write()
            elif msg == 'disable' or msg == 'off_4':
                self.enabled = False
                self.neopixel[0] = (0, 0, 0); self.neopixel.write()
            

        print('about to attempt MQTT connection')
        
        self.client = MQTTClient('ME35_aengus', mqtt_broker, port, keepalive=60)
        self.client.set_callback(callback)
        self.client.connect()
        self.client.subscribe(topic.encode())

        while True:
            self.client.check_msg()
            await asyncio.sleep(threadsleep)

    async def monitor_chord_buttons(self):
        while True:
            if self.enabled:
                if True: #if self.happy:
                    if not self.button4.value():
                        await self.send_chord('F#m')
                    if not self.button3.value():
                        await self.send_chord('Fm6')
                    if not self.button2.value():
                        await self.send_chord('Dm')
                    if not self.button1.value():
                        await self.send_chord('Cm')
                    if not self.button0.value():
                        await self.send_chord('Abm')
                else:
                    if not self.button0.value():
                        await self.send_chord('Cm')
                    if not self.button1.value():
                        await self.send_chord('Eb')
                    if not self.button2.value():
                        await self.send_chord('Fm')
                    if not self.button3.value():
                        await self.send_chord('Gm')
                    if not self.button4.value():
                        await self.send_chord('Ab')
            await asyncio.sleep(threadsleep)
    
    async def monitor_photoresistor(self):
        '''
        This method is never called in A6_orchestra
        '''
        while True:
            try:
                await asyncio.sleep(1)
                darkness_value = self.photoresistor.read_u16()
                # observed behavior:
                # the value is low when uncovered (between 128 and 192)
                # the value is higher when covered (between 592 and 800)
                print('DARKNESS VALUE: {}'.format(darkness_value))
                if darkness_value > 500:
                    self.enabled = False
                    topic = 'ME35-24/aengus'
                    msg = 'disable'
                    self.client.publish(topic.encode(), msg.encode())
                    print('just published disable')
                else:
                    self.enabled = True
                    topic = 'ME35-24/aengus'
                    msg = 'enable'
                    print('about to try to publish "enable"')
                    self.client.publish(topic.encode(), msg.encode())
                    print('just published enable')
            except AttributeError:
                print('AttributeError')
            await asyncio.sleep(threadsleep)

    # async def hallelujah(self):
    #     await self.send_chord('C')
    #     await asyncio.sleep(1.5)
    #     await self.send_chord('F')
    #     await asyncio.sleep(0.75)
    #     await self.send_chord('G')
    #     await asyncio.sleep(1.5)
    #     await self.send_chord('Am')
    #     await asyncio.sleep(1.5)
    #     await self.send_chord('F')
    #     await asyncio.sleep(1.5)
    #     await self.send_chord('G')
    #     await asyncio.sleep(1.5)
    #     await self.send_chord('Em')
    #     await asyncio.sleep(1.5)
    #     await self.send_chord('Am')
    #     await asyncio.sleep(4.5)

async def main():
    myft = FT()
    if USE_WIFI:
        await asyncio.gather(asyncio.create_task(myft.test()), 
                             asyncio.create_task(myft.monitor_mqtt_button()),
                             asyncio.create_task(myft.monitor_mqtt()),
                             asyncio.create_task(myft.monitor_chord_buttons())
                            )
    else:
        await asyncio.gather(asyncio.create_task(myft.test()), 
                             asyncio.create_task(myft.monitor_mqtt_button()),
                             asyncio.create_task(myft.monitor_chord_buttons())
                            )
    print('MMMMMMMMMMMABOUT TO DISCONNECT')
    myft.yeller.disconnect()

asyncio.run(main())