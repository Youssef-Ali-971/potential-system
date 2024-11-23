# imports
import machine
import math
import time
from time import sleep
from machine import ADC
from machine import Pin


#######################################
# Pin and constant definitions
#######################################
SEVEN_SEGMENT_START_PIN = 0
DISPLAY_COUNT = 4
DECIMAL_PRECISION = 3
sensors = ADC(26)
last_button_time_stamp = 0
button_1 = Pin(15, Pin.IN, Pin.PULL_DOWN)


# HEX values for 7 segment display values
digit_list_hex = [
    0b11000000,  # 0
    0b11111001,  # 1
    0x24,  # 2
    0x30,  # 3
    0x19,  # 4
    0x12,  # 5
    0x02,  # 6
    0x78,  # 7
    0x00,  # 8
    0x10,  # 9
]

#######################################
# Global variables
#######################################
button_pressed = False
display_value = 80
segment_pins = []
display_select_pins = []
current_display_index = DISPLAY_COUNT -1  # to keep track of which digit is currently being displayed

def scan_display():
    global current_display_index, display_value

    digit = display_value

    # Display the digit,
    # enable the decimal point if the current digit index equals to the set decimal precision
    display_digit(digit, current_display_index, current_display_index == DECIMAL_PRECISION and 0 != DECIMAL_PRECISION)

    # Move to the next display
    current_display_index = (current_display_index - 1)
    if current_display_index < 0:
        current_display_index = DISPLAY_COUNT -1

    for i in range(4):
        display_digit(int(digit % 10), i, i == DECIMAL_PRECISION and 0 != DECIMAL_PRECISION)
        time.sleep(0.03)
        digit /= 10

def display_digit(digit_value, digit_index, dp_enable=False):
    # Ensure the value is valid
    if digit_value < 0 or digit_value > len(digit_list_hex):
        #error
        return

    # Deselect all display select pins
    for pin in display_select_pins:
        pin.value(0)

    # Set the segments according to the digit value
    mask = digit_list_hex[digit_value]
    #mask = 0x0b11000000;
    for i in range(7):  # 7 segments from A to G
        segment_pins[i].value((mask >> i) & 1)

    # Set the DP if it's enabled
    segment_pins[7].value(1 if dp_enable == False else 0)

    # Otherwise, ensure the index is valid and activate the relevant display select pin
    if 0 <= digit_index < DISPLAY_COUNT:
        display_select_pins[digit_index].value(1)
    else:
        return

def interrupt_callback(pin): # A function to handle the button bouncing
    global last_button_time_stamp
    cur_button_ts = time.ticks_ms()
    button_press_delta = cur_button_ts - last_button_time_stamp
    if button_press_delta > 400:
        last_button_time_stamp = cur_button_ts
        global button_pressed
        button_pressed = True
button_1.irq(trigger=Pin.IRQ_FALLING, handler=interrupt_callback)

def sensor():   #The function to read the didgital value and convert it
    global sensors
    digital_val = sensors.read_u16()
    analog_val = float((digital_val/(2**16-1))*  3.3)
    global display_value
    display_value =int( analog_val * 1000)
    print("Voltage = ",display_value, "mv")
def main():
    global button_pressed, SEVEN_SEGMENT_START_PIN, DISPLAY_COUNT, display_value
    display_value = 0
    # Set up display select pins
    for i in range(SEVEN_SEGMENT_START_PIN + 8, SEVEN_SEGMENT_START_PIN + 8 + DISPLAY_COUNT):
        pin = machine.Pin(i, machine.Pin.OUT)
        pin.value(0)
        display_select_pins.append(pin)
    
    # Set up seven segment pins
    for i in range(SEVEN_SEGMENT_START_PIN, SEVEN_SEGMENT_START_PIN + 8):
        pin = machine.Pin(i, machine.Pin.OUT)
        pin.value(1)
        segment_pins.append(pin)
    if button_pressed is True:
        button_pressed = False
        sensor()
        
    while button_pressed == False:
        scan_display()
while True:
    main()
    
