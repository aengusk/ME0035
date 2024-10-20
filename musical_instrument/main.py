import time
from BLE_CEEO import Yell

NoteOn = 0x90
NoteOff = 0x80
StopNotes = 123
SetInstroment = 0xC0
Reset = 0xFF

velocity = {'off':0, 'pppp':8,'ppp':20,'pp':31,'p':42,'mp':53,
    'mf':64,'f':80,'ff':96,'fff':112,'ffff':127}
    
p = Yell('Fred', verbose = True, type = 'midi')
p.connect_up()
        
channel = 0
note = 55
cmd = NoteOn

channel = 0x0F & channel
timestamp_ms = time.ticks_ms()
tsM = (timestamp_ms >> 7 & 0b111111) | 0x80
tsL =  0x80 | (timestamp_ms & 0b1111111)

c =  cmd | channel     
payload = bytes([tsM,tsL,c,note,velocity['f']])

for i in range(5):
    p.send(payload)
    time.sleep(5)
p.disconnect()