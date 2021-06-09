# Maintenance

## Charge batteries

Note that these are LiPo batteries: please take care to avoid physical damage, especially puncturing batteries.

There are 2 chargers, 1 is the "spare". There are 5 batteries, one is the spare.

Once a week, replace the batteries in the rockers.

Charge the batteries in the "UltraLast" charger. The batteries can sit in the charger for a week. The LEDs in the charger turn green when the batteries are charged (a few hours).

## Test Rockers/Video

Every morning.

The videos should be playing on each projector, and the "background" audio should be playing.

Test each rocker switch, the hyper-directional speaker should get louder.

# Trouble-Shooting

## Video/Sound/Raspberry-Pi

Raspberry-Pi has a red LED indicating power.
And, when first turned on, the green LED will blink.

Shortly after power on, the Pi should start showing some stuff on the projector, eventually getting to a desktop with a log open.
Shortly after that, it blanks the screen and starts the video and audio.

### Blank screen

HDMI cable.
Projector power/on.
Raspberry-Pi power.

### No Audio

Cables. Sound is configured to come over the HDMI to the projector, and then split from the audio-out phono plug.
Note that the Right channel is a fixed volume ("background" sound on JBL and Mountains).
But, the Left channel will change volume (louder) when someone sits in the chair.

## Rocker

When the seat switch is open, the Arduino LED will flash about every 5 seconds. If it is not flashing, test the switch:

When the seat switch is closed (listen for click), the LED on the keyfob, and the LED on the Arduino will turn on. If not, replace battery.

If the switch does not clicking, adjust the screw that engages the switch arm (1/4 crescent wrench).

When the battery is replaced, the Arduino will restart: it does a sequence of LED blinks. If not, replace with a charged battery.

Try replacing the battery with the spare.

## Chargers

It should only take a few hours to charge the batteries.

Check that the battery is seated correctly, the "+" end is particularly problematic.

Check the wall-plug and where the usb at the charger.

Unplug and plug in the charger, the LEDs should immediately show red then possibly green. Switch chargers and wall-plugs.
