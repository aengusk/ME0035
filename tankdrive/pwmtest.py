from machine import Pin
import tankdrive

motors = tankdrive.Motors(Pin('P5', Pin.OUT), Pin('P4', Pin.OUT), Pin('P8', Pin.OUT), Pin('P7', Pin.OUT))

motors.drive(1, 1)