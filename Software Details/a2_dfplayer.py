# as per github and chatgpt
from machine import Pin, PWM, UART
import time


# initialize hscr04 and touch sensor
#dfplayer setup
uart = UART(2, baudrate=9600, tx=17, rx=16)


def df_cmd(cmd, p1, p2):
    """Sends HEX packet to DFPlayer."""
    packet = bytes([0x7E, 0xFF, 0x06, cmd, 0x00, p1, p2, 0xEF])
    uart.write(packet)

def play_sound(folder, track):
    """Plays track from specific folder."""
    df_cmd(0x0F, folder, track)

# --- INITIALIZATION ---
time.sleep(2) # Wait for DFPlayer boot
df_cmd(0x06, 0x00, 22) # Set Volume
last_proximity_trigger = 0 # To prevent sound spamming

while True:
   dist = get_distance()
   if dist < 50 and (time.time() - last_proximity_trigger) > 5:
        print(f"Intruder detected at {dist}cm! Squawking...")
        play_sound(1, 1) # Play 001.mp3 (Warning sound)
        last_proximity_trigger = time.time()

    # 2. TOUCH SENSOR CHECK (The "Head")
    if touch_sensor.value() == 1:
        start_time = time.ticks_ms()
        action_triggered = False
        
        while touch_sensor.value() == 1:
            duration = time.ticks_diff(time.ticks_ms(), start_time)
            
            if duration >= 3000:
                print("3s Hold: Interaction Sound")
                play_sound(1, 2) # Play 002.mp3 (Happy sound)
                action_triggered = True
                # Wait for user to let go
                while touch_sensor.value() == 1: time.sleep_ms(10)
            
            time.sleep_ms(10)

    time.sleep_ms(100) # Loop delay 