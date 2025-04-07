import RPi.GPIO as GPIO
import time

# Define GPIO to LCD mapping
LCD_RS = 5
LCD_E = 6
LCD_D4 = 13
LCD_D5 = 19
LCD_D6 = 26
LCD_D7 = 21

# Define some device constants
LCD_WIDTH = 16     # Maximum characters per line
LCD_CHR = True     # Mode - Sending data
LCD_CMD = False    # Mode - Sending command

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

def lcd_init():
    # Initialise display
    lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 001100 Display On, Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
    time.sleep(E_DELAY)

def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True  for character
    #        False for command

    GPIO.output(LCD_RS, mode)  # RS

    # High bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x10 == 0x10:
        GPIO.output(LCD_D4, True)
    if bits & 0x20 == 0x20:
        GPIO.output(LCD_D5, True)
    if bits & 0x40 == 0x40:
        GPIO.output(LCD_D6, True)
    if bits & 0x80 == 0x80:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

    # Low bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x01 == 0x01:
        GPIO.output(LCD_D4, True)
    if bits & 0x02 == 0x02:
        GPIO.output(LCD_D5, True)
    if bits & 0x04 == 0x04:
        GPIO.output(LCD_D6, True)
    if bits & 0x08 == 0x08:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

def lcd_toggle_enable():
    # Toggle enable
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)

def lcd_string(message, line):
    # Send string to display

    if line == 1:
        lcd_byte(0x80, LCD_CMD)
    if line == 2:
        lcd_byte(0xC0, LCD_CMD)

    for i in range(LCD_WIDTH):
        if i < len(message):
            lcd_byte(ord(message[i]), LCD_CHR)
        else:
            lcd_byte(ord(' '), LCD_CHR)

def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
    GPIO.setup(LCD_E, GPIO.OUT)  # E
    GPIO.setup(LCD_RS, GPIO.OUT) # RS
    GPIO.setup(LCD_D4, GPIO.OUT) # DB4
    GPIO.setup(LCD_D5, GPIO.OUT) # DB5
    GPIO.setup(LCD_D6, GPIO.OUT) # DB6
    GPIO.setup(LCD_D7, GPIO.OUT) # DB7

    # Initialise display
    lcd_init()

    while True:
        # Send some test
        lcd_string("     0    0     ", 1)
        lcd_string("        V       ", 2)

        time.sleep(3)  # 3 second delay

        # Send some test
        lcd_string("     o    0     ", 1)
        lcd_string("        ^       ", 2)

        time.sleep(3)

 # Send some test
        lcd_string("     o    o     ", 1)
        lcd_string("        ^       ", 2)

        time.sleep(3)

 # Send some test
        lcd_string("     o    o     ", 1)
        lcd_string("        .       ", 2)

        time.sleep(3)

 # Send some test
        lcd_string("     o    o     ", 1)
        lcd_string("        o       ", 2)

        time.sleep(3)
     
      # Send some test
        lcd_string("     O    O     ", 1)
        lcd_string("        o       ", 2)

        time.sleep(3)
                
                 # Send some test
        lcd_string("     o    o     ", 1)
        lcd_string("        3       ", 2)

        time.sleep(3)   
        
                         # Send some test
        lcd_string("     o    o     ", 1)
        lcd_string("        x       ", 2)

        time.sleep(3)   
        
if __name__ == '__main__':
    main()
