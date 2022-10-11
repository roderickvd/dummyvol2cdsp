#!/usr/bin/python

# dummyvol2cdsp v0.1.0 - Forward Alsa dummy device volume to CamillaDSP
# Copyright (c) 2022 Roderick van Domburg

##############################################################################
# Many DACs report an enormous but unusable volume range. This script uses a
# cubic mapping to maximize the usable range of the volume slider. 60 dB is a
# common and appropriate range of volume control. In environments with less
# background noise, such as headphones or treated studios, you may want to
# try as high as 90 dB. Sane values would be from 50-100.
VOL_RANGE = 60

# CamillaDSP IP address
CDSP_HOST = '127.0.0.1'

# CamillaDSP port number
CDSP_PORT = 1234

# Alsa dummy device name
DUMMY_DEV = 'hw:Dummy'

# Alsa dummy mixer control name
DUMMY_CTL = 'Master'
##############################################################################

from alsaaudio import Mixer
from camilladsp import CamillaConnection

import select

mixer = Mixer(device=DUMMY_DEV, control=DUMMY_CTL)
cdsp = CamillaConnection(CDSP_HOST, CDSP_PORT)

MIN_NORM = pow(10, (-1.0 * VOL_RANGE / 60.0))

def map_cubic_volume(alsavol):
    pct = float(alsavol)/100.0
    cubic_vol = pow(pct * (1.0 - MIN_NORM) + MIN_NORM, 3) * VOL_RANGE - VOL_RANGE
    return cubic_vol

def cdsp_set_volume(dbvol):
    if not cdsp.is_connected():
        cdsp.connect()
        
    cdsp.set_volume(dbvol)
    
    if abs(dbvol) >= VOL_RANGE:
        cdsp.set_mute(True)
    elif cdsp.get_mute():
        cdsp.set_mute(False)
        
def sync_volume():
   # assume that channel volume is equal
   alsavol = mixer.getvolume()[0]
   cubicvol = map_cubic_volume(alsavol)
   print('alsa=%d%% cubic=%.1f dB' % \
       (alsavol, cubicvol))
   try:
       cdsp_set_volume(cubicvol)
   except Exception as err:
       print('setting cdsp volume failed: {0}'.format(err))
       pass

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
