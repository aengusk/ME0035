from machine import ADC, Pin
import time

# Initialize the ADC (on GPIO 34 for ESP32 or A0 for ESP8266)
adc = ADC(Pin('GPIO27', Pin.PULL_UP))  # Replace 34 with the correct pin number for your microcontroller

# Set the width (optional, ESP32 specific)
#adc.width(ADC.WIDTH_12BIT)  # Set the resolution to 12-bit (0-4095)

# Set the attenuation (ESP32 specific, to extend the voltage range)
#adc.atten(ADC.ATTN_11DB)  # Allows reading up to 3.3V (ESP32)

# For ESP8266, just create the ADC object directly like this:
# adc = ADC(0)  # Pin A0 is used for analog reads on ESP8266

while True:
    # Read the analog value
    light_value = adc.read_u16()
    
    # Print the light intensity
    print("Light Intensity:", light_value)
    
    # Delay to avoid flooding the output
    time.sleep(1)
