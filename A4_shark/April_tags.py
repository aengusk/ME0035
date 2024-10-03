
#Imports
import time
import network
import sensor
import math
from mqtt import MQTTClient



#Reset Sensor settings
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)  
sensor.set_auto_whitebal(False) 
clock = time.clock()



#Wifi Connection
SSID = "Tufts_Robot"  
KEY = ""  

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, KEY)

while not wlan.isconnected():
    print('Trying to connect to "{:s}"...'.format(SSID))
    time.sleep_ms(1000)


print("WiFi Connected ", wlan.ifconfig())


#MQTT setup
client = MQTTClient("ME35_Rex", 'broker.hivemq.com', port=1883)
client.connect()


#Looks for april tag orientation and publishs it
while True:
    clock.tick()
    img = sensor.snapshot()
    for tag in img.find_apriltags():
        img.draw_rectangle(tag.rect, color=(255, 0, 0))
        img.draw_cross(tag.cx, tag.cy, color=(0, 255, 0))
        rotation = (180 * tag.rotation) / math.pi
        print_args = (tag.name, tag.id, rotation)
        client.publish("ME35-24/Rex", str(rotation))
        print("Tag Family %s, Tag ID %d, rotation %f (degrees)" % print_args)
    #print(clock.fps())
