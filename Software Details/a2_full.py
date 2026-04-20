from machine import Pin, PWM, time_pulse_us
import time

#initialize
#servo
s_lr = PWM(Pin(13, Pin.OUT), freq(50))
s_ud = PWM(Pin(12, Pin.OUT), freq(50))

# hcsr04
trig1 = (Pin 13, Pin.OUT)
trig2 = (Pin 13, Pin.OUT)
echo1 = (Pin 13, Pin.OUT)
echo2 = (Pin 13, Pin.OUT)

# touch sensor ttp223
touch_sensor = Pin(4, Pin.IN)

#gear servo motor mg995
gear = PWM(Pin(4), freq(50)) #needs external power supply

W_U = 150
W_D = 30
W_SP = 0.005

HEAD_UP = 70
HEAD_DOWN = 110
last_proximity_time = 0



#dfplayer setup
uart = UART(2, baudrate=9600, tx=17, rx=16)

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


# function for head nod
def set_angle(motor, angle):
    duty = int(((angle / 180) * 100) + 26)
    s_ud.duty(duty)
def head_nod(cycles=3 ):
    for z in range(cycles):
      set_angle(s_ud, HEAD_UP)
      time.sleep(0.3)
      set_angle(s_ud, HEAD_DOWN)
      time.sleep(0.3)
    set_angle(s_ud, 90)  

# functions for dfplayer
def df_cmd(cmd, p1, p2):
    """Sends HEX packet to DFPlayer."""
    packet = bytes([0x7E, 0xFF, 0x06, cmd, 0x00, p1, p2, 0xEF])
    uart.write(packet)

def play_sound(folder, track):
    """Plays track from specific folder."""
    df_cmd(0x0F, folder, track)
    
# dfplayer functions---chgpt
def df_cmd(cmd, p1, p2):
    packet = bytes([0x7E, 0xFF, 0x06, cmd, 0x00, p1, p2, 0xEF])
    uart.write(packet)

def play_sound(track):
    df_cmd(0x0F, 0x01, track) # Folder 01, Track X



#main loop   
 
 set_angle(gear, 90)
set_angle(s_lr, 90)
set_angle(s_ud, 90)
time.sleep(2)
df_cmd(0x06, 0x00, 20)


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
            
     
set_wing_angle(90)


    if touch_sensor.value() == 1:
        start_time = time.ticks_ms()
        long_press = False
        
        
        while touch_sensor.value() == 1:
            elapsed = time.ticks_diff(time.tick_ms() , start_time)
            
            if elapsed >= 3000:
                flap_cycle(cycle=5)
                long_press = True
                play_sound(2)
                print('only flap')
                while touch_sensor.value() == 1: time.sleep_ms(10)
                
            if elapsed >= 5000:
                flap_cycles(cycle=8)
                play_sound(2)
                head_nod(cycles=3)
                long_press = True
                print('flap and nod')
                
                
                while touch_sensor == 1:
                    time.sleep_ms(10)
                    
                    
            time.sleep_ms(10)
            
            
            
        if not long_press:
            print('press longer')
            
            
    time.sleep_ms(50)
            
            
            
            
        
    

    
    
    

