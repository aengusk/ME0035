from machine import Pin, PWM
import sensor
import time
import math

class Motors:
    '''
    example usage:
                    lf,      lb,      rf,      rb
    motors = Motors(Pin(27), Pin(26), Pin(19), Pin(21))
    motors.drive(1.0, -1.0)
    '''
    def __init__(self, lf, lb, rf, rb):
        self.pwm_LF = PWM(lf)
        self.pwm_LF.freq(20000)
        self.pwm_LF.duty_u16(0) # can be any positive integer 0-1023

        self.pwm_LB = PWM(lb)
        self.pwm_LB.freq(20000)
        self.pwm_LB.duty_u16(0) # can be any positive integer 0-1023

        self.pwm_RF = PWM(rf)
        self.pwm_RF.freq(20000)
        self.pwm_RF.duty_u16(0) # can be any positive integer 0-1023

        self.pwm_RB = PWM(rb)
        self.pwm_RB.freq(20000)
        self.pwm_RB.duty_u16(0) # can be any positive integer 0-1023

    def drive(self, left, right): # where each is a float between -1.0 and 1.0
        '''
        test cases to catch:
        both arguments must be numbers
        if the numbers are out of range, round them into range
        '''
        print('about to drive motors with {}, {}'.format(left, right))
        assert isinstance(left, float) or isinstance(left, int)
        assert isinstance(right, float) or isinstance(right, int)
        if left < -1:
            left = -1
        if left > 1:
            left = 1
        if right < -1:
            right = -1
        if right > 1:
            right = 1
        if left == 0: # stop both left ones
            self.pwm_LF.duty_u16(0)
            self.pwm_LB.duty_u16(0)
        elif left > 0: # left forward
            self.pwm_LF.duty_u16(int(65535 * left))
            self.pwm_LB.duty_u16(0)
        elif left < 0: # left backward
            self.pwm_LF.duty_u16(0)
            self.pwm_LB.duty_u16(int(-65535 * left))
        if right == 0: # stop both right ones
            self.pwm_RF.duty_u16(0)
            self.pwm_RB.duty_u16(0)
        elif right > 0: # right forward
            self.pwm_RF.duty_u16(int(65535 * right))
            self.pwm_RB.duty_u16(0)
        elif right < 0: # right backward
            self.pwm_RF.duty_u16(0)
            self.pwm_RB.duty_u16(int(-65535 * right))

    def interpret_throttle_angle(throttle, angle):
        if angle == 0:
            return throttle, throttle
        if 0< angle < 180:
            return throttle, throttle*(1-angle/45)
        if 180 < angle:
            return throttle*((angle-315)/45), throttle
        raise AssertionError('l_r_f_s final block flow reach error')


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA) # changing to QVGA (320x240) from QQVGA, makes it slower
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)  # must turn this off to prevent image washout...
sensor.set_auto_whitebal(False)  # must turn this off to prevent image washout...
clock = time.clock()

# f_x is the x focal length of the camera. It should be equal to the lens focal length in mm
# divided by the x sensor size in mm times the number of pixels in the image.
# The below values are for the OV7725 camera with a 2.8 mm lens.

# f_y is the y focal length of the camera. It should be equal to the lens focal length in mm
# divided by the y sensor size in mm times the number of pixels in the image.
# The below values are for the OV7725 camera with a 2.8 mm lens.

# c_x is the image x center position in pixels.
# c_y is the image y center position in pixels.

f_x = (2.8 / 3.984) * 160  # find_apriltags defaults to this if not set
f_y = (2.8 / 2.952) * 120  # find_apriltags defaults to this if not set
c_x = 160 * 0.5  # find_apriltags defaults to this if not set (the image.w * 0.5)
c_y = 120 * 0.5  # find_apriltags defaults to this if not set (the image.h * 0.5)


def degrees(radians):
    return (180 * radians) / math.pi


while True:
    clock.tick()
    img = sensor.snapshot()
    for tag in img.find_apriltags(
        fx=f_x, fy=f_y, cx=c_x, cy=c_y
    ):  # defaults to TAG36H11
        img.draw_rectangle(tag.rect, color=(255, 0, 0))
        img.draw_cross(tag.cx, tag.cy, color=(0, 255, 0))
        print_args = (
            tag.x_translation,
            tag.y_translation,
            tag.z_translation,
            degrees(tag.x_rotation),
            degrees(tag.y_rotation),
            degrees(tag.z_rotation),
        )
        # Translation units are unknown. Rotation units are in degrees.
        #print(tag.x_translation)
        #print("Tx: %f, Ty %f, Tz %f, Rx %f, Ry %f, Rz %f" % print_args)
        current_angle = tag.x_translation # range -7 to 7
        current_dist = -1 * tag.z_translation
        target_angle = 0 # car should turn right when angle is negative, left when angle is positive
        target_dist = 10
        #kp_vel =
        #kp_steer =
        throttle = kp_vel * (current_dist - target_dist)
        angle = kp_steer * (current_angle - target_angle)
    #print(clock.fps())


motors = Motors(Pin('P5', Pin.OUT), Pin('P4', Pin.OUT), Pin('P8', Pin.OUT), Pin('P7', Pin.OUT))


motors.drive(*motors.interpret_throttle_angle(1, 0)) # straignt, 0 angle
