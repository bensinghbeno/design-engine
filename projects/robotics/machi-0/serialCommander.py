import serial
import time

# Change to the port your Arduino is connected to
SERIAL_PORT = '/dev/ttyACM0'   # e.g. 'COM3' on Windows, '/dev/ttyUSB0' on Linux
BAUD_RATE = 115200

# Open serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Give Arduino time to reset after connection

def send_command(cmd):
    ser.write(cmd.encode())
    print(f"Sent command: {cmd}")

def menu():
    print("\n--- Motor Control Menu ---")
    print("0: Stop")
    print("1: Reverse")
    print("2: Forward")
    print("3: Left Turn")
    print("4: Right Turn")
    print("q: Quit")

menu()

while True:
    key = input("Enter command: ").strip()
    if key in ['0', '1', '2', '3', '4']:
        send_command(key)
    elif key.lower() == 'q':
        send_command('0')  # Stop before quitting
        break
    else:
        print("Invalid input. Try again.")

ser.close()
