#!/usr/bin/env python

# g_audio2hqplayer v0.1.0 - Forward UAC2 Gadget device volume to HQPlayer
# Copyright (c) 2024 Roderick van Domburg

##############################################################################
# Alsa UAC2 Gadget device name
ALSA_DEV = 'hw:UAC2Gadget'

# Alsa UAC2 Gadget mixer control name
ALSA_CTL = 'PCM'

# HQPlayer hostname
HQPLAYER_HOST = 'localhost'

# HQPlayer maximum volume
HQPLAYER_MAX_VOL = -3

# HQPlayer minimum volume
HQPLAYER_MIN_VOL = -60
##############################################################################

from alsaaudio import Mixer
import os, select

mixer = Mixer(device=ALSA_DEV, control=ALSA_CTL)
        
def sync_volume():
   alsavol = mixer.getvolume()[0]
   pct = float(alsavol) / 100.0
   vol = HQPLAYER_MIN_VOL + pct * abs(HQPLAYER_MAX_VOL - HQPLAYER_MIN_VOL)
   os.system("hqp5-control %s --volume %.0f" % (HQPLAYER_HOST, vol))

if __name__ == '__main__':
    # synchronize on initial startup
    sync_volume()
    
    # handle volume changes
    poll = select.poll()
    descriptors = mixer.polldescriptors()
    poll.register(descriptors[0][0])    
    while True:
        poll.poll()
        mixer.handleevents()
        sync_volume()
