import machine
import time
import random
from machine import Pin, PWM, UART

SERVO_HZ        = 50

YAW_CENTER      = 1500
YAW_LEFT        = 900
YAW_RIGHT       = 2100
YAW_HARD_LEFT   = 700
YAW_HARD_RIGHT  = 2300

TILT_CENTER     = 1500
TILT_UP         = 1100
TILT_DOWN       = 1800

WING_REST       = 1500
WING_OPEN       = 850
WING_FULL       = 620

DETECT_RANGE_CM   = 100
CLOSE_RANGE_CM    = 30
DETECT_CONFIRM_MS = 3000

TOUCH_DEBOUNCE_MS  = 600
SOUND_COOLDOWN_MS  = 4500
VOL_LEVEL          = 24

IDLE_SOUND_MIN_MS  = 18000
IDLE_SOUND_MAX_MS  = 40000
IDLE_SCAN_MIN_MS   = 1800
IDLE_SCAN_MAX_MS   = 4500

TALK_CHECK_MS      = 22000
TALK_CHANCE_PCT    = 25

FOLDER_TOUCH  = 1;  TRACKS_TOUCH  = 6
FOLDER_TALK   = 2;  TRACKS_TALK   = 4
FOLDER_MOTION = 3;  TRACKS_MOTION = 5
FOLDER_IDLE   = 4;  TRACKS_IDLE   = 4

DUR_TOUCH  = 3000
DUR_TALK   = 3500
DUR_MOTION = 2500
DUR_IDLE   = 2000

trig_l = Pin(5,  Pin.OUT)
echo_l = Pin(18, Pin.IN)
trig_r = Pin(19, Pin.OUT)
echo_r = Pin(21, Pin.IN)

touch_pin = Pin(22, Pin.IN)

pwm_yaw   = PWM(Pin(23), freq=SERVO_HZ, duty=0)
pwm_tilt  = PWM(Pin(25), freq=SERVO_HZ, duty=0)
pwm_wings = PWM(Pin(26), freq=SERVO_HZ, duty=0)

uart = UART(2, baudrate=9600, tx=17, rx=16)

def us_to_duty(us):
    """Convert servo pulse width µs → 10-bit duty. Period = 20 000 µs at 50 Hz."""
    return max(0, min(1023, int(us * 1023 // 20000)))

def write_servo(pwm_obj, us):
    pwm_obj.duty(us_to_duty(us))

def sweep(pwm_obj, from_us, to_us, steps=25, step_ms=13):
    """Smooth sweep between two positions."""
    delta = (to_us - from_us) / steps
    for i in range(steps + 1):
        write_servo(pwm_obj, int(from_us + delta * i))
        time.sleep_ms(step_ms)
    write_servo(pwm_obj, to_us)

# Track current head position for smooth relative movements
head_pos = {'yaw': YAW_CENTER, 'tilt': TILT_CENTER}

def move_head(yaw_us, tilt_us, spd=13):
    """Sweep both head axes simultaneously. Updates head_pos tracker."""
    steps = 25
    dy = (yaw_us  - head_pos['yaw'])  / steps
    dt = (tilt_us - head_pos['tilt']) / steps
    for i in range(steps + 1):
        write_servo(pwm_yaw,  int(head_pos['yaw']  + dy * i))
        write_servo(pwm_tilt, int(head_pos['tilt'] + dt * i))
        time.sleep_ms(spd)
    head_pos['yaw']  = yaw_us
    head_pos['tilt'] = tilt_us

def head_center(spd=14):
    move_head(YAW_CENTER, TILT_CENTER, spd)

def head_nod():
    """Natural nod: dip down → lift → settle."""
    move_head(head_pos['yaw'], TILT_DOWN,   16)
    time.sleep_ms(110)
    move_head(head_pos['yaw'], TILT_UP,     13)
    time.sleep_ms(80)
    move_head(head_pos['yaw'], TILT_CENTER, 17)

def idle_scan():
    """Small random head drift — keeps the bird looking alive in idle."""
    ny = YAW_CENTER  + random.randint(-300, 300)
    nt = TILT_CENTER + random.randint(-100, 150)
    ny = max(750,  min(2250, ny))
    nt = max(1250, min(1780, nt))
    move_head(ny, nt, 22)  

def wings_rest():
    write_servo(pwm_wings, WING_REST)

def wing_flap(flaps=3):
    """MG996R drives ornithopter through complete open/close cycles."""
    for _ in range(flaps):
        sweep(pwm_wings, WING_REST, WING_FULL, steps=14, step_ms=18)
        time.sleep_ms(130)
        sweep(pwm_wings, WING_FULL, WING_OPEN, steps=8,  step_ms=14)
        time.sleep_ms(90)
        sweep(pwm_wings, WING_OPEN, WING_REST, steps=16, step_ms=16)
        time.sleep_ms(110)
    wings_rest()

def measure_cm(trig, echo, timeout_us=28000):
    """
    Trigger HC-SR04, measure echo pulse, return distance in cm or None.

    VOLTAGE DIVIDER REQUIRED on every ECHO pin:
        HC-SR04 ECHO → [1kΩ] → GPIO → [2kΩ] → GND
    Output ≈ 5 × (2/3) = 3.33 V — safe for ESP32.
    Without this the 5 V echo will damage the GPIO over time.
    """
    trig.value(0);  time.sleep_us(2)
    trig.value(1);  time.sleep_us(10)
    trig.value(0)

    t0 = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), t0) > timeout_us:
            return None
    t_hi = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), t_hi) > timeout_us:
            return None
    return round(time.ticks_diff(time.ticks_us(), t_hi) * 0.0343 / 2, 1)

def read_sensors():
    """
    Read both sensors. Returns (side, dist_cm) or (None, None).
    side: 'left' | 'right' | 'center'
    30 ms gap prevents acoustic crosstalk between sensors.
    """
    left  = measure_cm(trig_l, echo_l)
    time.sleep_ms(30)
    right = measure_cm(trig_r, echo_r)

    lv = left  is not None and left  <= DETECT_RANGE_CM
    rv = right is not None and right <= DETECT_RANGE_CM

    if not lv and not rv:
        return None, None
    if lv and rv:
        if abs(left - right) < 12:
            return 'center', min(left, right)
        return ('left', left) if left < right else ('right', right)
    return ('left', left) if lv else ('right', right)


def df_send(cmd, p1=0, p2=0):
    """Send a 10-byte DFPlayer command packet over UART2."""
    ck  = (-(0xFF + 0x06 + cmd + 0x00 + p1 + p2)) & 0xFFFF
    pkt = bytes([0x7E, 0xFF, 0x06, cmd, 0x00,
                 p1, p2,
                 (ck >> 8) & 0xFF, ck & 0xFF, 0xEF])
    uart.write(pkt)
    time.sleep_ms(30)

def df_init():
    """Reset DFPlayer and set volume."""
    time.sleep_ms(1200)
    df_send(0x0C)               
    time.sleep_ms(600)
    df_send(0x06, 0, VOL_LEVEL) 
    time.sleep_ms(100)

def df_play(folder, track):
    """Play folder/track (1-indexed)."""
    df_send(0x0F, folder, track)

snd_state = {
    'last_ms'    : 0,
    'busy_until' : 0,
    'last_track' : {1: 0, 2: 0, 3: 0, 4: 0},
}

def can_play():
    """True when cooldown has elapsed and previous sound has finished."""
    now = time.ticks_ms()
    return (time.ticks_diff(now, snd_state['last_ms'])    >= SOUND_COOLDOWN_MS and
            time.ticks_diff(now, snd_state['busy_until']) >= 0)

def sound_done():
    return time.ticks_diff(time.ticks_ms(), snd_state['busy_until']) >= 0

def pick_track(folder, max_track):
    """Random non-repeating track selection within a folder."""
    last    = snd_state['last_track'][folder]
    choices = [t for t in range(1, max_track + 1) if t != last]
    if not choices:
        choices = list(range(1, max_track + 1))
    return random.choice(choices)

def play_sound(folder, max_track, duration_ms):
    """
    Play a random track from a folder. Respects cooldown timing.
    Returns True if triggered, False if blocked.

    Trigger → folder mapping:
      touch interaction → folder 01 (6 tracks, excited / greeting)
      pseudo-talking    → folder 02 (4 tracks, learning-to-listen phrases)
      motion detection  → folder 03 (5 tracks, curious / alert)
      idle ambient      → folder 04 (4 tracks, quiet / preening)
    """
    if not can_play():
        return False
    track = pick_track(folder, max_track)
    df_play(folder, track)
    now = time.ticks_ms()
    snd_state['last_ms']              = now
    snd_state['busy_until']           = time.ticks_add(now, duration_ms)
    snd_state['last_track'][folder]   = track
    return True


STATE_IDLE        = 0
STATE_DETECTING   = 1
STATE_INTERACTING = 2
STATE_TALKING     = 3

state = STATE_IDLE

timers = {
    'detect_start'  : 0,
    'detect_fired'  : False,
    'last_touch'    : 0,
    'last_scan'     : 0,
    'next_scan'     : 2500,
    'last_idle_snd' : 0,
    'next_idle_snd' : 20000,
    'last_talk'     : 0,
}

def handle_touch():
    """
    Touch trigger — HIGHEST priority.
    Faces user → 2 s realism pause → random action + sound from folder 01.

    Action-to-sound mapping (all from folder 01):
      nod only  → soft chirp track
      flap only → energetic track
      both      → expressive track
    The track is randomised within folder 01 regardless of action.
    """
    global state
    state = STATE_INTERACTING

    head_center(14)
    time.sleep_ms(2000)             
    action = random.choice(['nod', 'flap', 'both'])

    if action == 'nod':
        play_sound(FOLDER_TOUCH, TRACKS_TOUCH, DUR_TOUCH)
        time.sleep_ms(350)
        head_nod()

    elif action == 'flap':
        play_sound(FOLDER_TOUCH, TRACKS_TOUCH, DUR_TOUCH)
        time.sleep_ms(250)
        wing_flap(3)

    else:
        play_sound(FOLDER_TOUCH, TRACKS_TOUCH, DUR_TOUCH)
        time.sleep_ms(300)
        head_nod()
        time.sleep_ms(200)
        wing_flap(2)

    time.sleep_ms(600)
    wings_rest()
    head_center(16)
    timers['last_touch'] = time.ticks_ms()
    timers['last_scan']  = time.ticks_ms()
    state = STATE_IDLE


def handle_motion(side, dist_cm):
    """
    Motion reaction — MEDIUM priority.
    Plays folder 03 sound, then turns head toward closer sensor.
    Tilts up if object is very close.
    """
    target_yaw = YAW_CENTER
    if   side == 'left':  target_yaw = YAW_HARD_LEFT
    elif side == 'right': target_yaw = YAW_HARD_RIGHT

    target_tilt = TILT_UP if dist_cm < CLOSE_RANGE_CM else TILT_CENTER

    play_sound(FOLDER_MOTION, TRACKS_MOTION, DUR_MOTION)  
    time.sleep_ms(320)
    move_head(target_yaw, target_tilt, 13)


def handle_talking():
    """
    Pseudo-talking episode — LOW priority, fires stochastically in idle.
    Plays folder 02 "learning-to-listen" pre-recorded lines.
    Bird has NO microphone — these lines acknowledge that limitation:
    e.g. 'I can hear you moving but not your words yet'.
    2–3 phrases with engaged head movement between each.
    """
    global state
    state = STATE_TALKING

    for _ in range(random.randint(2, 3)):
        play_sound(FOLDER_TALK, TRACKS_TALK, DUR_TALK) 
        yo = random.randint(-180, 180)
        to = random.randint(-80, 100)
        move_head(YAW_CENTER + yo, TILT_CENTER + to, 19)
        time.sleep_ms(700)
        move_head(YAW_CENTER, TILT_CENTER, 21)
        time.sleep_ms(2800)    

    timers['last_talk'] = time.ticks_ms()
    state = STATE_IDLE


def handle_idle_sound():
    """Folder 04 ambient sound — no movement, bird is quietly alive."""
    play_sound(FOLDER_IDLE, TRACKS_IDLE, DUR_IDLE)   # folder 04
    timers['last_idle_snd'] = time.ticks_ms()
    timers['next_idle_snd'] = random.randint(IDLE_SOUND_MIN_MS, IDLE_SOUND_MAX_MS)


def main():
    global state

    print("=== Animatronic Bird — Booting ===")

    write_servo(pwm_yaw,   YAW_CENTER)
    write_servo(pwm_tilt,  TILT_CENTER)
    write_servo(pwm_wings, WING_REST)

    df_init()
    print("[BOOT] DFPlayer initialised")
    print("[BOOT] All servos centred")

    # Stagger timers so nothing fires simultaneously on boot
    now = time.ticks_ms()
    timers['last_scan']     = now
    timers['next_scan']     = random.randint(IDLE_SCAN_MIN_MS, IDLE_SCAN_MAX_MS)
    timers['last_idle_snd'] = now
    timers['next_idle_snd'] = random.randint(12000, 25000)
    timers['last_talk']     = now
    timers['last_touch']    = now

    print("[BOOT] Entering idle — bird is alive\n")

    while True:
        now      = time.ticks_ms()
        touched  = touch_pin.value() == 1
        touch_ok = time.ticks_diff(now, timers['last_touch']) > TOUCH_DEBOUNCE_MS

        
        if touched and touch_ok and state not in (STATE_INTERACTING, STATE_TALKING):
            print("[EVENT] Touch triggered")
            handle_touch()
            continue

       
        side, dist = read_sensors()
        detected   = side is not None

       
        if state == STATE_IDLE:

            if detected:
                state = STATE_DETECTING
                timers['detect_start'] = now
                timers['detect_fired'] = False
                print("[STATE] IDLE → DETECTING  side=%s  dist=%.1fcm" % (side, dist))

            else:
                # Idle head scan
                if time.ticks_diff(now, timers['last_scan']) >= timers['next_scan']:
                    idle_scan()
                    timers['last_scan'] = time.ticks_ms()
                    timers['next_scan'] = random.randint(IDLE_SCAN_MIN_MS, IDLE_SCAN_MAX_MS)

                # Idle ambient sound (folder 04)
                if (sound_done() and
                        time.ticks_diff(now, timers['last_idle_snd']) >= timers['next_idle_snd']):
                    print("[EVENT] Idle ambient sound (folder 04)")
                    handle_idle_sound()

                # Pseudo-talking check (folder 02)
                if (sound_done() and
                        time.ticks_diff(now, timers['last_talk']) >= TALK_CHECK_MS):
                    if random.randint(0, 99) < TALK_CHANCE_PCT:
                        print("[EVENT] Pseudo-talking episode (folder 02)")
                        handle_talking()
                        continue
                    timers['last_talk'] = now

   
        elif state == STATE_DETECTING:

            if not detected:
                print("[STATE] DETECTING → IDLE (object left)")
                head_center(18)
                state = STATE_IDLE
                timers['detect_fired'] = False

            else:
                elapsed = time.ticks_diff(now, timers['detect_start'])
                if elapsed >= DETECT_CONFIRM_MS and not timers['detect_fired']:
                    print("[EVENT] Motion confirmed  side=%s  dist=%.1fcm" % (side, dist))
                    timers['detect_fired'] = True
                    handle_motion(side, dist)   

                elif timers['detect_fired'] and sound_done():
                    ty = YAW_CENTER
                    if side == 'left':  ty = YAW_HARD_LEFT
                    if side == 'right': ty = YAW_HARD_RIGHT
                    if abs(ty - head_pos['yaw']) > 250:
                        move_head(ty, head_pos['tilt'], 21)

    
        elif state in (STATE_INTERACTING, STATE_TALKING):
            state = STATE_IDLE

        time.sleep_ms(75)   

if __name__ == '__main__':
    main()
