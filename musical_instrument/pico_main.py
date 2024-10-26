# Python
import time
import asyncio
# MicroPython
from machine import Pin, ADC, reset # type: ignore (suppresses Pylance lint warning)
import network                      # type: ignore (suppresses Pylance lint warning)
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

volumes = {'off':0, 'pppp':8,'ppp':20,'pp':31,'p':42,'mp':53,
    'mf':64,'f':80,'ff':96,'fff':112,'ffff':127}

chords = {
    'Am': (76,72,69),       'Ab': (75,72,68), 
    'G': (74,71,67),        'Gm': (74,70,67), 
    'F': (72,69,65),        'Fm': (72,68,65), 
    'Em': (71,67,64),       'Eb': (70,67,63), 
    'C': (67,64,60),        'Cm': (67,63,60)
}
class FT:
    def __init__(self):
        self.enabled = True
        self.happy = True
        
        self.button = Pin('GPIO20', Pin.IN, Pin.PULL_UP)

        self.photoresistor = ADC(Pin('GPIO27', Pin.PULL_UP))

        self.button0 = Pin('GPIO0', Pin.IN, Pin.PULL_UP)
        self.button1 = Pin('GPIO1', Pin.IN, Pin.PULL_UP)
        self.button2 = Pin('GPIO2', Pin.IN, Pin.PULL_UP)
        self.button3 = Pin('GPIO3', Pin.IN, Pin.PULL_UP)
        self.button4 = Pin('GPIO4', Pin.IN, Pin.PULL_UP)
        
        #self.connect_to_wifi()
        
        self.yeller = Yell("AengusFT", verbose = True, type = 'midi')
        self.yeller.connect_up()
        print('just finished connecting up to Bluetooth')

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
                self.happy = not self.happy
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
        mqtt_broker = 'broker.hivemq.com' # or 'broker.emqx.io'
        port = 1883
        topic = 'ME35-24/aengus'

        def callback(topic, msg):
            topic, msg = topic.decode(), msg.decode()
            print('received MQTT message {}'.format(msg))

            # try: 
            #     msg = eval(msg)
            # except NameError:
            #     pass
            # print('the message was of type {}'.format(type(msg)))
            # if isinstance(msg, float) or isinstance(msg, int):
            #     self.angle = float(msg)
            #     print('set angle to {}'.format(float(msg)))
            # elif isinstance(msg, tuple) and len(msg) == 2:
            #     #self.drive_motors(*msg)
            #     if msg[0] > msg[1]:
            #         self.throttle = 1.0
            #     else:
            #         self.throttle = 0.0

            # elif isinstance(msg, str):
            #     if msg == 'forward':
            #         self.throttle = 1.0
            #         print('set throttle to 1')
            #     elif msg == 'backward':
            #         self.throttle = -1.0
            #         print('set throttle to -1')
            #     elif msg == 'stop':
            #         self.throttle = 0.0
            #         print('set throttle to 0')
            #     else: 
            #         print("the message was an unknown string {}".format(msg))
        print('about to attempt MQTT connection')
        
        client = MQTTClient('ME35_aengus', mqtt_broker, port, keepalive=60)
        client.set_callback(callback)
        client.connect()
        client.subscribe(topic.encode())

        while True:
            client.check_msg()
            # try:
            #     client.check_msg()
            # except OSError:
            #     print('OSError WAS RAISED')
            #     self.neopixel[0] = (10, 10, 0); self.neopixel.write()
            #     reset()
            #     # recall self.connect_to_wifi here?
            await asyncio.sleep(threadsleep)

    async def monitor_chord_buttons(self):
        while True:
            if self.enabled:
                if self.happy:
                    if not self.button0.value():
                        print('C was pressed')
                        await self.send_chord('C')
                    if not self.button1.value():
                        await self.send_chord('Em')
                    if not self.button2.value():
                        await self.send_chord('F')
                    if not self.button3.value():
                        await self.send_chord('G')
                    if not self.button4.value():
                        await self.send_chord('Am')
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
        while True:
            darkness_value = self.photoresistor.read_u16()
            # observed behavior:
            # the value is low when uncovered (between 128 and 192)
            # the value is higher when covered (between 592 and 800)
            print('DARKNESS VALUE: {}'.format(darkness_value))
            if darkness_value > 15000:
                self.enabled = False
            else:
                self.enabled = True
            await asyncio.sleep(1)
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
    await asyncio.gather(asyncio.create_task(myft.test()), 
                         asyncio.create_task(myft.monitor_mqtt_button()),
                         #asyncio.create_task(myft.monitor_mqtt()),
                         asyncio.create_task(myft.monitor_chord_buttons()), 
                         asyncio.create_task(myft.monitor_photoresistor())
                        )
    print('MMMMMMMMMMMABOUT TO DISCONNECT')
    myft.yeller.disconnect()

asyncio.run(main())