from numpy import interp
import time
import sched
from math import ceil
import mido
from pythonosc import dispatcher
from pythonosc import osc_server

outs = mido.get_output_names()

print('Select a MIDI OUT port:')
count = 0
for o in outs:
    print('[',count,']:\t', o)
    count += 1

s = int(input('--> '))

port_name = outs[s]

print('Sending MIDI to \'', port_name, '\'')

outport = mido.open_output(port_name)

in_midi_note = 60
play_midi_note = 60

run_state = False
us_clock_itvl = (60*10**6)/(24*120)

#create mido messages
msg_note_on = mido.Message('note_on', note=60)
msg_note_off = mido.Message('note_off', note=60) 
msg_start = mido.Message('start')
msg_stop = mido.Message('stop')
msg_clock = mido.Message('clock')

def cv_to_midi_handler(unused_addr, args, V):
    global in_midi_note
    try:
        if V >= -5 and V <= 5: 
            # interpolate the Volts value in the relative MIDI note value
            in_midi_note = int(round(interp(V, [-5,5], [0,120])))
    except ValueError: pass

def note_gate_handler(unused_addr, args, G):
    global in_midi_note
    try:
        if G == 0.0:
            #print("NOTE OFF", msg_note_off.note , G)
            outport.send(msg_note_off)
        else:
            play_midi_note = in_midi_note
            msg_note_on.note = play_midi_note
            msg_note_off.note = play_midi_note
            #print("NOTE ON", msg_note_on.note, V)
            outport.send(msg_note_on)

    except ValueError: pass


# EXPERIMENTAL!! (i.e. it doesn't work yet)

msg_sched = sched.scheduler(time.time, time.sleep)
pt = time.time()
def send_clock():
    global pt
    outport.send(msg_clock)
    # schedule new event
    msg_sched.enter(us_clock_itvl/10**6, 1, send_clock)
    #print('clock')
    #now = time.time()
    #print(now-pt)
    #pt = now


def bpm_cv_handler(unused_addr, args, V):
    try:
        global us_clock_itvl

        if V <= 1.32 and V >= -2.00:
            bpm = int(round(120 * 2**V))
            
            us_clock_itvl = (60*10**6)/(24*bpm)
            print(V, bpm, us_clock_itvl)
            """
            msg_tempo = mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm))
            msg_start = mido.Message('start')
            print(msg_tempo, msg_start)
            outport.send(msg_tempo)
            #outport.send(msg_start)
            """

    except ValueError: pass

def run_trig_handler(unused_addr, args, T):
    global run_state
    try:
        
        if T > 0.0:
            run_state = not run_state
            print('Run', run_state)
            if run_state:
                print('Clock @', us_clock_itvl/10**6)
                # msg_sched.enter(us_clock_itvl/10**6, 1, send_clock)
                outport.send(msg_start)
                # outport.send(msg_clock) #send first clock together with start msg
                # msg_sched.run()
                
            else:
                # clear the event queue (for already scheduled clock events)
                list(map(msg_sched.cancel, msg_sched.queue))
                # stop the clock
                outport.send(msg_stop)
    except ValueError: pass

def clock_handler(unused_addr, args, G):
    try:
        if G == 10.0:
            outport.send(msg_clock)

    except ValueError: pass




dispatcher = dispatcher.Dispatcher()
dispatcher.map("/trowacv/ch/1", cv_to_midi_handler, 'Volts')
dispatcher.map("/trowacv/ch/2", note_gate_handler, 'Gate')
dispatcher.map("/trowacv/ch/3", bpm_cv_handler, 'Bpm')
dispatcher.map("/trowacv/ch/4", run_trig_handler, 'Run')
dispatcher.map("/trowacv/ch/5", clock_handler, 'Clock')
#dispatcher.map("/logvolume", print_compute_handler, "Log volume", math.log)


server = osc_server.ThreadingOSCUDPServer(('127.0.0.1', 7000), dispatcher)
server.serve_forever()

