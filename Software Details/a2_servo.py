#code for servo motor movnt to move head according to distance measured by hcsr04 
from machine import Pin, PWM, time_pulse_us
import time

#initialize
s_lr = PWM(Pin(13, Pin.OUT), freq(50))
s_ud = PWM(Pin(13, Pin.OUT), freq(50))

trig1 = (Pin 13, Pin.OUT)
trig2 = (Pin 13, Pin.OUT)
echo1 = (Pin 13, Pin.OUT)
echo2 = (Pin 13, Pin.OUT)


#function calculates distance 
def calc_distance(trig, echo):
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    while echo1.value() == 0:
        pass
    while echo.value() == 0:
        pass
    t1 = time.ticks_us()
    while echo.value() == 1:
        pass
    t2 = time.ticks_us()
    return (time.ticks_diff(t2, t1) * 0.0343) / 2 #speed of sound


def move_servo(lr_angle, ud_angle) :
    global current_lr, current_ud
    lr_angle = max(40, min(140, lr_angle))
    ud_angle = max(70, min(110, ud_angle))
    s_lr.duty(int(((y_angle / 180) * 100) + 26))
    s_ud.duty(int(((p_angle / 180) * 100) + 26))
    
    current_lr = lr_angle
    current_ud = ud_angle
    
#main loop   
    
print('Blu is observing')

while True:
    dist_left = calc_distance(trig1, echo1)
    time.sleep_ms(10) 
    dist_right = calc_distance(trig2, echo2)
    
    if dist_left < 100 or dist_right < 100:
        if dist_left < (dist_right - 5):
            current_lr += 2
            
        elif dist_right < (dist_left - 5):
            current_lr -= 2
            
            
        if dist_left < 30 or dist_right < 30:
            current_ud = 75 
        else:
            current_ud = 90
            
        else:
        if current_lr > 90:
            current_lr -= 1
        if current_lr < 90:
            current_lr += 1
        current_ud = 90
        
        update_motors(current_lr, current_ud)
        
        
        time.sleep_ms(50)
        
        print('obs working')
            
    
    

    
    
    
