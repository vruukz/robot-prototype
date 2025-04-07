import time
import RPi.GPIO as GPIO
import pygame

# Hardware Configuration
MOTOR_CONFIG = {
    'left': {
        'enable': 17,    # EN1 pin
        'input1': 22,    # IN1 pin
        'input2': 23     # IN2 pin
    },
    'right': {
        'enable': 27,    # EN2 pin
        'input1': 8,     # IN3 pin
        'input2': 25     # IN4 pin
    }
}

# Movement Parameters
MIN_SPEED = 30    # Minimum speed to prevent gear stalling
MAX_SPEED = 100   # Maximum allowed speed
ACCEL_STEP = 5    # Increased speed change step
DIRECTION_DELAY = 0.05  # 50ms safety delay for direction changes

class TrackedVehicle:
    def __init__(self):
        self.current_speed = 80  # Start at 100% speed
        self.last_direction = None
        self._initialize_gpio()
        self._setup_motors()

    def _initialize_gpio(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for side in ['left', 'right']:
            config = MOTOR_CONFIG[side]
            GPIO.setup(config['enable'], GPIO.OUT)
            GPIO.setup(config['input1'], GPIO.OUT)
            GPIO.setup(config['input2'], GPIO.OUT)

    def _setup_motors(self):
        self.motors = {}
        for side in ['left', 'right']:
            config = MOTOR_CONFIG[side]
            self.motors[side] = {
                'pwm': GPIO.PWM(config['enable'], 1000),
                'in1': config['input1'],
                'in2': config['input2']
            }
            self.motors[side]['pwm'].start(100)  # Start at full speed

    def _control_motor(self, side, direction):
        motor = self.motors[side]
        if direction == 'forward':
            GPIO.output(motor['in1'], GPIO.HIGH)
            GPIO.output(motor['in2'], GPIO.LOW)
        elif direction == 'backward':
            GPIO.output(motor['in1'], GPIO.LOW)
            GPIO.output(motor['in2'], GPIO.HIGH)
        else:  # Stop
            GPIO.output(motor['in1'], GPIO.LOW)
            GPIO.output(motor['in2'], GPIO.LOW)
        
        motor['pwm'].ChangeDutyCycle(self.current_speed)

    def move(self, left_dir, right_dir):
        if (left_dir, right_dir) != self.last_direction:
            self.stop_motors()
            time.sleep(DIRECTION_DELAY)
        
        self._control_motor('left', left_dir)
        self._control_motor('right', right_dir)
        self.last_direction = (left_dir, right_dir)

    def stop_motors(self):
        for side in ['left', 'right']:
            self._control_motor(side, 'stop')

    def adjust_speed(self, increment):
        new_speed = self.current_speed + increment
        self.current_speed = max(MIN_SPEED, min(MAX_SPEED, new_speed))
        for side in ['left', 'right']:
            self.motors[side]['pwm'].ChangeDutyCycle(self.current_speed)

    def shutdown(self):
        self.stop_motors()
        for side in ['left', 'right']:
            self.motors[side]['pwm'].stop()
        GPIO.cleanup()

def main():
    vehicle = TrackedVehicle()
    pygame.init()
    screen = pygame.display.set_mode((240, 160))
    pygame.display.set_caption("Tracked Robot Controller")
    clock = pygame.time.Clock()

    print("Robot Control System Active")
    print("Controls:")
    print("W/S: Backward/Forward (Reversed)")
    print("A/D: Rotate Left/Right")
    print("UP/DOWN: Adjust Speed")
    print("Q: Quit")

    speed_change = 0
    last_speed_update = 0
    motor_ensure_counter = 0  # Counter to ensure both motors move

    try:
        while True:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    raise KeyboardInterrupt

            # Get key states
            keys = pygame.key.get_pressed()

            # Movement logic with reversed W/S and corrected A/D
            if keys[pygame.K_w]:
                # REVERSED: W now means backward
                vehicle.move('forward', 'forward')
                motor_ensure_counter = 5  # Force motor check for next 5 frames
            elif keys[pygame.K_s]:
                # REVERSED: S now means forward
                vehicle.move('backward', 'backward')
                motor_ensure_counter = 5
            elif keys[pygame.K_a]:
                # Left turn - only right motor moves forward
                vehicle.move('backward', 'forward')
            elif keys[pygame.K_d]:
                # Right turn - only left motor moves forward
                vehicle.move('forward', 'backward')
            else:
                vehicle.stop_motors()

            # Motor ensure logic - double checks both motors are getting commands
            if motor_ensure_counter > 0:
                motor_ensure_counter -= 1
                current_dir = vehicle.last_direction
                if current_dir == ('backward', 'backward') or current_dir == ('forward', 'forward'):
                    vehicle.move(*current_dir)  # Re-send command

            # Speed control
            speed_change = 0
            if keys[pygame.K_UP]:
                speed_change += ACCEL_STEP
            if keys[pygame.K_DOWN]:
                speed_change -= ACCEL_STEP

            # Apply speed changes with rate limiting
            current_time = pygame.time.get_ticks()
            if current_time - last_speed_update > 100:
                if speed_change != 0:
                    vehicle.adjust_speed(speed_change)
                    print(f"Current Speed: {vehicle.current_speed}%")
                    last_speed_update = current_time

            clock.tick(30)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        vehicle.shutdown()
        pygame.quit()

if __name__ == "__main__":
    main()
