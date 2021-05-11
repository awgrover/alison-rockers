"""
Run 2 videos: "A" and "B". Files video-a.xxx and video-b.xxx.
Turn sound on/off for each to follow its signal.

There are 2 signals, logically "A" and "B".

We are using the PT2272 receiver https://cdn-shop.adafruit.com/datasheets/PT2272.pdf, 
as a breakout module: https://www.adafruit.com/product/1096
"""
    
# https://www.raspberrypi.org/documentation/usage/gpio/
from gpiozero import Button
import time
class Receiver:
    """
    Provides:
    .is_on
    Which become true when the signal is seen,
    and then stays true for n seconds,
    resetting n everytime a signal is seen.
    """

    def __init__(self, duration=5, pin=14):
        self.duration = duration
        self.receiver = Button(pin, active_state=True, pull_up=True, bounce_time=None) # high for signal
        self.receiver.when_pressed( restart_signal )
        self.timer = 0
        self.was = False

    def restart_signal():
        self.timer = time.time() + self.duration

    def is_on(self):
        return self.timer >= time.time()

    def changed_to(self):
        """True if changed to true, False if changed to false, None if no change"""
        if self.was == self.is_on:
            return None
        else
            self.was = self.is_on
            return self.is_on

# 14 & 15 are next to gnd/5v/3v
rocker_a = Receiver(14)
rocker_b = Receiver(15)

while(True):
    x = rocker_a.changed_to()
    if x == None:
        pass
    elif x:
        print("A Fade in")
    else:
        print("A Fade out"

    x = rocker_b.changed_to()
    if x == None:
        pass
    elif x:
        print("B Fade in")
    else:
        print("B Fade out")

    sleep(0.01) # let "interrupts" happen
