import pyautogui
import time

# Set the coordinates of the click position
x=1340
y=614
# Set the time interval between each click in seconds
interval = 1

# # Infinite loop to continuously click
while True:
    pyautogui.click(x=x, y=y)
    time.sleep(interval)
# print(pyautogui.position())

