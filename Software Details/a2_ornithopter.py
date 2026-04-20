#wing movmt based on touch sensor ttp223
from machine import Pin, PWM
import time

touch_sensor = Pin(4, Pin.IN)
gear = PWM(Pin(14), freq=50) #needs external power supply

W_U = 150
W_D = 30
W_SP = 0.005

# function sets wing angle
def set_wing_angle(angle):
    duty = int(((angle / 180) * 100) + 26) #(angle/180 * 100 + 26) is a safe range for ESP32 acc to google
    gear.duty(duty)

# function for flap movement
def flap_cycle(cycle = 5):
    print('flap working')
    
    for x in range(cycles):
        for angle in range(W_U, W_D, -5)
        time.sleep(W_SP)
        
        for angle in range(W_U, W_D, 5)
        time.sleep(W_SP * 1.5)
        
        
    set_wing_angle(90)
    



#main loop
    
set_wing_angle(90)

while True:
    if touch_sensor.value() == 1:
        start_time = time.ticks_ms()
        long_press = False
        
        
        while touch_sensor.value() == 1:
            elapsed = time.ticks_diff(time.tick_ms() , start_time)
            
            if elapsed >= 3000:
                flap_cycle(cycle=5)
                long_press = True
                
                
                while touch_sensor == 1:
                    time.sleep_ms(15)
                    
                    
            time.sleep_ms(15)
            
            
            
        if not long_press:
            print('press longer')
            
                    
    time.sleep_ms(50)
            
            
            
            
            
            
            
            
            
            