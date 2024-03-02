# dummyvol2cdsp

Forwards Alsa dummy device volume to CamillaDSP.

## Description

This is a Python script that runs in the background, monitoring the Alsa dummy mixer control and forwarding its volume setting to CamillaDSP over a websocket. It also provides a cubic volume control to maximise the usable range of the volume sliders.

It was developed to have loudness compensated volume control for various Linux audio players.

## Getting Started

### Dependencies

* A Linux system with working Alsa, CamillaDSP and Python 3 configurations
* [pyalsaaudio](https://pypi.org/project/pyalsaaudio/) >= v0.9.2
* [pycamilladsp](https://github.com/HEnquist/pycamilladsp)

### Installing

You must have root access and know your way around the command line.

#### Alsa dummy driver

First, set up the Alsa dummy driver. Later we will use its mixer control as a proxy to CamillaDSP's volume filters.

```
# echo "options snd-dummy fake_buffer=0 pcm_substreams=1" >> /etc/modprobe.d/snd_dummy.conf
# echo "snd-dummy" >> /etc/modules-load.d/modules.conf
```

_Note:_ although you do not need any of the dummy's PCM streams or substreams, do not set them to 0. Doing so will cause the system to hang on reboot, and you will need to reinstall or recover on another system.

Now reboot and verify that the dummy driver is set up correctly:
```
# reboot
# aplay -l
**** List of PLAYBACK Hardware Devices ****
card 0: Dummy [Dummy], device 0: Dummy PCM [Dummy PCM]
 Subdevices: 1/1
 Subdevice #0: subdevice #0
# amixer -c 0 scontrols
Simple mixer control 'Master',0
Simple mixer control 'Synth',0
Simple mixer control 'Line',0
Simple mixer control 'CD',0
Simple mixer control 'Mic',0
Simple mixer control 'External I/O Box',0
```

_Optional:_ make the dummy mixer control the system-wide default. This helps to immediately show the dummy mixer controls with `amixer` and `alsamixer`, for example:
```
# echo "defaults.ctl.card 0" >> /etc/alsa/conf.d/00-defaults.conf
# chmod a+x /etc/alsa/conf.d/00-defaults.conf
```

#### CamillaDSP loudness filters

Now at the other end of the chain we add volume filters to CamillaDSP. You can use a `Volume` filter or a `Loudness` filter. The loudness filter in fact is a volume filter, but with extra parameters and functionality to apply loudness correction when the volume is lowered.

The relevant configuration lines are as follows:
```
devices:
 chunksize: 1024
 queuelimit: 1
filters:
 loudnessvol:
   type: Loudness
   parameters:
     ramp_time: 200.0
     reference_level: -10.0
     high_boost: 3.0
     low_boost: 8.5
pipeline:
- type: Filter
 channel: 0
 names:
 - loudnessvol
- type: Filter
 channel: 1
 names:
 - loudnessvol
 ```

A few notes on these values:

* Recommended values for `chunksize` are `1024` for 44.1/48 kHz, `2048` for 88.2/96 kHz, `4096` for 176.4/192 kHz, and so on.
* A `queuelimit` of `1` ensures the lowest audio latency to user input.
* The `ramptime` gently increases or decreases the volume for the given duration in milliseconds. This prevents popping noises that could by caused by abrupt volume changes. `200` milliseconds is a sane default.
* The `reference_level` very much depends on your audio chain, source material and personal preferences. You may try values between `0` and `30`.
* The `high_boost` and `low_boost` were chosen as averages from the ISO 226 equal-loudness contours. Again this depends on your needs and preferences, and plays along with the chosen `reference_level`.
* If you have other mixers or filters, `loudnessvol` should be last in the pipeline.
* Only if your output device is limited to 16-bit audio, you may choose to add a `Dither` filter after `loudnessvol` in the pipeline.

#### Audio players

Now configure audio players to use the dummy mixer control.

**Warning:** during this step turn your amplifier off -- risk of damage and/or injury!
If you start playback at this stage, it will output at full volume and the volume slider will do nothing yet.

A few examples:

##### bluez-alsa

Launch with `--mixer hw:Dummy`. Requires `bluez-alsa` v4.0.0 or higher. 

##### librespot

Launch with `--mixer alsa --alsa-mixer-device hw:Dummy --alsa-mixer-control Master`.

##### MPD

Edit `/etc/mpd.conf` to contain the following lines:

```
audio_output {
    ...
    mixer_type "hardware"
    mixer_control “Master”
    mixer_device "hw:Dummy”
    mixer_index "0"
    ...
}
```

##### shairport-sync

Edit the following lines in `/etc/shairport-sync.conf`. The lines are commented by the default, uncomment them:

```
mixer_control_name = “Master”;
mixer_device = "hw:Dummy”;
```

_Note:_ although the dummy mixer registers as a hardware mixer, it does not support hardware mute. Keep `use_hardware_mute_if_available` set to `no`.

#### dummyvol2cdsp

* Download [`dummyvol2cdsp.py`](https://github.com/roderickvd/dummyvol2cdsp/blob/main/dummyvol2cdsp.py)
* Make it executable: `chmod a+x /path/to/dummyvol2cdsp.py`

At the top of the script, there are some user-configurable settings. The defaults should be sane.

### Executing program

First time, execute `dummyvol2cdsp` to start testing:

```
# /path/to/dummyvol2cdsp.py
```

Open another terminal, launch `alsamixer` and change the volume of the dummy mixer. You should now see the script printing lines like `alsa=49% cubic=-50.5 dB`. If it also prints along the lines of `setting cdsp volume failed: [Errno 111] Connection refused`, that means that CamillaDSP is not running yet. A likely cause is that playback has not started yet (regardless of whether an audio player is connected or not).

If you see volume settings being printed without errors, then look at the CamillaDSP GUI via the web interface and change the volume again. Under "Volume" at the left, you should see the volume changes coming in.

Now everything is working, hit Ctrl+C to exit. Then edit `/etc/rc.local` to launch `dummyvol2cdsp` in the background when booting:

```
# Forward Alsa dummy mixer volume to CamillaDSP
/path/to/dummyvol2cdsp.py > /dev/null 2>&1 &
```

Finally, reboot and verify that volume changes are still being forwarded to CamillaDSP.

If you have convinced yourself volume changes are coming in properly, you can now turn up the amplifier again -- in small steps, just as a final precaution. Congratulations, you have yourself a working loudness corrected volume control!

## Help

* If you hear audio from one channel only, or the channels are out of balance, check if you have added the `loudnessvol` filter to the pipeline twice: once for each channel.
* Please [report](https://github.com/roderickvd/dummyvol2cdsp/issues) any bugs you find.
* Do not open issues for general help or installation questions.

## Authors

* [Roderick van Domburg](https://github.com/roderickvd)

## Version History

All notable changes to this project will be documented in this paragraph.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### [0.1.1] - 2024-03-02

#### Added

- Companion `g_audio2hqplayer.py` to forward UAC2 Gadget volume to HQPlayer.

#### Changed

- Use Python from environment instead of system Python.

### [0.1.0] - 2022-10-11

#### Added

- Initial release.

[0.1.0]: https://github.com/roderickvd/dummyvol2cdsp/releases/tag/v0.1.0

## License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/roderickvd/dummyvol2cdsp/blob/main/LICENSE) file for details.

## Acknowledgments

* [alsa_cdsp](https://github.com/scripple/alsa_cdsp)
* [CamillaDSP](https://github.com/HEnquist/camilladsp)
* [HOWTO: Soekris dam1021 DAC and MPD on Raspberry Pi](http://raw-sewage.net/articles/dam1021-raspberry-pi)