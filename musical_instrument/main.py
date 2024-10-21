import time
from BLE_CEEO import Yell # type: ignore (suppresses Pylance lint warning)
from machine import Pin # type: ignore (suppresses Pylance lint warning)
import asyncio

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
        
        self.button0 = Pin('GPIO10', Pin.IN, Pin.PULL_UP)
        self.button1 = Pin('GPIO11', Pin.IN, Pin.PULL_UP)
        self.button2 = Pin('GPIO12', Pin.IN, Pin.PULL_UP)
        self.button3 = Pin('GPIO13', Pin.IN, Pin.PULL_UP)
        self.button4 = Pin('GPIO14', Pin.IN, Pin.PULL_UP)
        
        
        self.yeller = Yell("AengusFT", verbose = True, type = 'midi')
        self.yeller.connect_up()
        print('just finished connecting up')

    async def test(self):
        testiter = 0
        while True:
            testiter += 1
            await asyncio.sleep(1)
            print(testiter)
            await asyncio.sleep(threadsleep)

    def send_chord(self, chord, volume = 96):
        '''
        chord: a str in chords.keys()
        '''
        for note in chords[chord]:
            self.send_note(note, volume = volume)


    def send_note(self, note, volume = 96):
        '''
        note: an integer MIDI note according to 
        https://forum.metasystem.io/forum/metagrid-pro/beta/issues/2981-c-2-c-1-midi-notes-lower-keyboard-range-question
        observed behavior: 55 -> G2 so 60 -> C3
        '''
        channel = 0
        #note = 55
        cmd = NoteOn

        channel = 0x0F & channel
        timestamp_ms = time.ticks_ms()
        tsM = (timestamp_ms >> 7 & 0b111111) | 0x80
        tsL =  0x80 | (timestamp_ms & 0b1111111)

        c =  cmd | channel     
        payload = bytes([tsM,tsL,c,note,volume])
        self.yeller.send(payload)

    async def monitor_buttons(self):
        while self.enabled:
            if self.happy:
                if not self.button0.value():
                    self.send_chord('C')
                if not self.button1.value():
                    self.send_chord('Em')
                if not self.button2.value():
                    self.send_chord('F')
                if not self.button3.value():
                    self.send_chord('G')
                if not self.button4.value():
                    self.send_chord('Am')
            else:
                if not self.button0.value():
                    self.send_chord('Cm')
                if not self.button1.value():
                    self.send_chord('Eb')
                if not self.button2.value():
                    self.send_chord('Fm')
                if not self.button3.value():
                    self.send_chord('Gm')
                if not self.button4.value():
                    self.send_chord('Ab')
            await asyncio.sleep(threadsleep)
    
    async def hallelujah(self):
        self.send_chord('C')
        await asyncio.sleep(1.5)
        self.send_chord('F')
        await asyncio.sleep(0.75)
        self.send_chord('G')
        await asyncio.sleep(1.5)
        self.send_chord('Am')
        await asyncio.sleep(1.5)
        self.send_chord('F')
        await asyncio.sleep(1.5)
        self.send_chord('G')
        await asyncio.sleep(1.5)
        self.send_chord('Em')
        await asyncio.sleep(1.5)
        self.send_chord('Am')
        await asyncio.sleep(4.5)

async def main():
    myft = FT()
    await asyncio.gather(asyncio.create_task(myft.test()), 
                            asyncio.create_task(myft.monitor_buttons())
                        )
    print('MMMMMMMMMMMABOUT TO DISCONNECT')
    myft.yeller.disconnect()

asyncio.run(main())