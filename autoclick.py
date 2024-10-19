import pyautogui
import time

# Set the coordinates of the click position
x=1278
y=828

# Set the time interval between each click in seconds
interval = 5

# Infinite loop to continuously click
while True:
    pyautogui.click(x=x, y=y)
    time.sleep(interval)
