from machine import Pin, PWM
import time

# Pin Assignments
touch_sensor = Pin(4, Pin.IN)
gear = PWM(Pin(14), freq=50) #needs extrenal

W_U = 150  # Up position
W_D = 30   # Down position
W_SP = 0.01 # Speed (seconds)

def set_wing_angle(angle):
    duty = int(((angle / 180) * 102) + 26) 
    gear.duty(duty)

def flap_cycle(cycles=5):
    print('Flapping started')
    for _ in range(cycles):
        # movedown
        for angle in range(W_U, W_D, -10):
            set_wing_angle(angle)
            time.sleep(W_SP)
        # moveup
        for angle in range(W_D, W_U, 10):
            set_wing_angle(angle)
            time.sleep(W_SP)
    set_wing_angle(90) # Return to neutral
    print('Flapping finished')

# Initial State
set_wing_angle(90)

# Main Loop
while True:
    if touch_sensor.value() == 1:
        start_time = time.ticks_ms()
        long_press = False
        
        # Debounce/Wait to detect long press
        while touch_sensor.value() == 1:
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            
            if elapsed >= 3000: # 3-second threshold
                flap_cycle(cycles=5)
                long_press = True
                
                # Wait for user to release button
                while touch_sensor.value() == 1:
                    time.sleep_ms(50)
            
            time.sleep_ms(20)
            
        if not long_press:
            print('Press longer (3s) to trigger flap')
            
    time.sleep_ms(100)