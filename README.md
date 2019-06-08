# OSC-to-MIDI
A simple script to receive notes and gates messages over Open Sound Control (OSC) and send MIDI commands to external hardware.

## How to use it
This script was conceived to create MIDI commands from CV values generated in VCV Rack and sent over OSC, through the almighty cvOSCcv module. 

### Setup:
- Load cvOSCcv into VCV Rack
- Connect the CV output of your sequencer/note generator to the Value input of `/ch/1` as if it is a 1 oct/CV input and the gate source to `/ch/2`.
- Connect your Run gate output to `/ch/4`, in order to start/stop the clock on the external hardware. This will invert the value of a boolean variable that is used to track the running/idle state of the clock, whenever a gate is received. NOTE: the initial state is idle, so make sure that your clock is not running when launching this script.
- Connect the MIDI clock trigger to `/ch/5`. Depending on the synchronization method used by your external hardware, this should be x24 times the frequency of your BPM settings. 
- Launch your script with explicit niceness, in order to get decent timing: 
`sudo nice -n -15 python3 path-to-script/osc-to-midi.py` (see notes at the end for further details).
At startup, the script will ask you to specify which MIDI OUT interface you want to send MIDI messages to.
- Click on `Config` button on cvOSCcv and then `Enable` the OSC client

![Setup Example](example.png)

### Notes about MIDI Clock
I mainly tested this feature on MacOS.

The `/ch/3` was initially devoted to receive the BPM CV-out value from Clocked module. The MIDI clock messages were sent by the script itself using `sched` package in python, at an interval defined by the BPM value. Although I wasn't able to send such messages at a stable rate, probably due to a bug in the code or process priority settings. Therefore, I decided to trigger the MIDI clock messages using Rack itself, as described above. 

As a side note, I noticed that if I launched Ableton Live before Rack, I was getting more timely and stable clock on the external hardware by using the same script. Probably Live has better control over the external audio interface (an old EMU 0404 USB, using unofficial driver, in this case), but I need to further investigate this behavior. Also, when Live is launched, Rack's clock DOUBLED its rate, so I had to send x12 MIDI clock triggers instead of x24 usual rate.
