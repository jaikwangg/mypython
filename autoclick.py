import pyautogui
import time
import ctypes

X = 1278
Y = 1000
INTERVAL = 0.1
START_DELAY = 5
STOP_KEY = "Q"


def is_key_pressed(key):
    return ctypes.windll.user32.GetAsyncKeyState(ord(key)) & 0x8000


pyautogui.PAUSE = 0

print(f"Starting in {START_DELAY} seconds...")
time.sleep(START_DELAY)
print(f"Clicking every {INTERVAL} seconds. Press {STOP_KEY.lower()} to stop.")

while not is_key_pressed(STOP_KEY):
    pyautogui.click(x=X, y=Y)
    time.sleep(INTERVAL)

print("Stopped.")
