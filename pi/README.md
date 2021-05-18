# "PI" Component: Ceiling/Video/Sound

A raspberry PI runs a video, responds to the RF signal to control the sound.

2 instances, "A" and "B", aka "comet" and "coal".

## Principles

* no software configuration to distinguish A vs B: a hardware jumper.
* visible state/diagnostics (on screen, and LEDs).
* split video vs sound into separate processes.
* default accessible on the network
* minimize configuration (e.g. zeroconf, etc)
* consider security to be a fairly low concern.
* programs should self-diagnose requirements, etc.

## Pi

I choose to use raspberry pi 3 B+. This does require a micro-hdmi to standard HDMI adapter.

## Pi-OS Configuration

Use the standard raspbian OS, image install on a SD Card. I choose a 32GB card to have plenty of room for videos.
*Version Used* : 2021-03-04-raspios-buster-armhf-full

* I assume python3, with the raspberry PI GPIO/etc libraries.
* I assume 'lxterminal' opens a GUI terminal window
* I assume `pactl` for pulse-audio volume control.
* I assume `zenity` for alerts/status

### 1st Boot Configuration

* hostname: "alisona" and "alisonb"
* choose a new password, same for both a/b.
* Video "yes I can see black border" (aka turn overscan on)
* VNC server on : for convenience
* SSH server on

### Configure vnc server

It's not quite compatible with standard Remina client, so:

* configure as "vnc password", use same password as linux login.

### Disable screen saver

We want videos to play without screen-saver activating.

* Edit /etc/xdg/lxsession/LXDE-pi/autostart
    @xset s off
    @xset -dpms

## Configure SSH

It does the reverse-dns lookup, which we don't care about and wastes time.

* Edit /etc/ssh/sshd_config
    useDNS no

## Enable mDNS

We want to get to the Pi using a mDNS name (*.local),
and we might as well let it advertise so we can confirm
it's appearence on the local network.

* Edit /etc/avahi/avahi-daemon.conf
    # this makes any hostname.local refer to hosts on your lan reachable via mdns
    domain-name=local
    # they are apparently turned off as default, i'd guess for privacy / security reasons
    # this broadcast your hostname and hostinfo on the lan via mdns
    publish-hinfo=yes
    publish-workstation=yes

## Additional Packages

* apt install mirage

## Remote Access

Setup your ssh to access alisona.local, and alisonb.local

## Application Code

Copy the rocker/ directory to the raspberry pi:
    scp -pr rocker/ alisona.local:~/pi/rocker

## Init, aka Startup

.....


## Videos

Place 2 videos in ~/pi/rocker:

* The "A" video should be named "A-*", i.e. starts with "A-"
* The "B" video should be named "B-*", i.e. starts with "B-"
* There should be _exactly_ one file that starts with "A-" and one that starts with "B-".
* We can apparently play most movies, including .mov, .mp4, .ogg, etc.

## WiFi on site

Before installation in the ceiling, connect each Pi to a keyboard, mouse, and monitor/projector and configure WiFi access.

Confirm that it appears on mDNS: otherwise, later debugging, etc., will be inconvenient.

### Options w/o mDNS

* use the IP address 
* configure the PI as a hotspot
* use a CAT5 ethernet cable
* use keyboard/mouse/monitor and operate _from_ the Pi
* edit the sc-card on your development machine

## Correspondance With Rockers

See also, the README for the rockers.

The keyfobs for the rockers are hardwired as "A" and "B".
Set the Pi's jumper (below) to correspond.

The correspondance relies on the "data" (D0..D3) value of the RF system, so
a Pi will only respond to the A fob, or the B fob, and play the corresponding video.

keyfob -> pi-receiver + pi-jumper -> pi-video

### Jumper Setup: "A" vs "B"

Refer to <this image> to designate the Pi as "A" vs "B". When the jumper is on pins 37&XX, the
pi is designated as "B", otherwise as "A".

## Receiver Wiring

See the xxxcode, and README_SETUP.md document.

## Video/Audio Connections

See the README_SETUP.md document.
