# Marantz / Denon AVR (Telnet) for Home Assistant

A local-push integration that keeps one telnet connection (port 23) open to a
Marantz or Denon receiver and exposes **everything the receiver reports** as
entities. Built and checked against a Marantz NR1607 (firmware 3700-4058-3044);
other Denon/Marantz models that speak the same protocol should work, and any
value they report that this integration doesn't know yet still shows up as a
(disabled) `Raw …` diagnostic sensor.

## What you get

**Media players**: main zone and zone 2 (power, volume, mute, source,
sound mode). Source names follow the renames on the receiver, and the source
list only shows inputs that are enabled in the receiver's setup.

**Sensors** (about 150 on an NR1607), updated the moment the receiver reports a change:

| Group | Examples |
|---|---|
| Status | Power, main zone, volume (0–98 and dB), mute, input, video input, sound mode, sound mode category, sleep timer, auto standby, ECO, display dimmer |
| Incoming signal | Audio input signal code, sample rate, channel format, input/output video resolution, audio input mode, digital input mode |
| Audio settings | Tone control, bass, treble, dynamic compression, LFE, MultEQ, Dynamic EQ, reference level, Dynamic Volume, Cinema EQ, dialog level, subwoofer level, audio delay, Neural:X, loudness management, M-DAX, graphic EQ, headphone EQ… |
| Channel levels | One sensor per active channel (main zone and zone 2), in dB |
| Video | Aspect, output resolution, HDMI resolution, HDMI audio output, video processing mode |
| Zone 2 | Power, volume, mute, input, sleep, auto standby, channel levels |
| Tuner | Frequency, preset, band, tuning mode |
| Display | The 9 lines of the on-screen display (online music / USB / Bluetooth "now playing") |
| Diagnostics | Model, friendly name, AVR and DTS firmware, speaker configuration and sizes, speaker calibration trims per channel, HDMI control settings, lip sync, power amp assign, menu language, setup lock, trigger output, last message |

**Controls**: selects (ECO, dimmer, MultEQ, Dynamic Volume, DRC, reference level,
audio input mode, video processing, HDMI audio out, aspect, auto standby),
switches (Dynamic EQ, Cinema EQ, tone control, loudness management, dialog/subwoofer
level adjust, Neural:X, graphic/headphone EQ, trigger 1…), numbers (bass, treble,
LFE, dialog level, subwoofer level, audio delay, sleep timers, tuner preset,
every channel level). Controls only appear for settings the receiver reports.

**Service** `marantz_telnet.send_command`: send any raw command (or a list),
e.g. `PSDYNEQ ON`, `MSMOVIE`, `TPAN05`.

## Install

### HACS (custom repository)
1. Put this folder in a GitHub repository (the repository root must contain
   `hacs.json` and `custom_components/`).
2. HACS → ⋮ → Custom repositories → add the repository URL, type *Integration*.
3. Install **Marantz / Denon AVR (Telnet)** and restart Home Assistant.

### Manual
Copy `custom_components/marantz_telnet` into your Home Assistant
`config/custom_components/` folder and restart.

### Set up
Settings → Devices & services → Add integration → *Marantz / Denon AVR (Telnet)*,
then enter the receiver's IP address (port 23).

## Important

* **The receiver accepts only one telnet connection.** Close any other telnet
  client (PuTTY, the bridge script, or the built-in *Denon AVR* integration with
  telnet enabled) before adding this integration, or the connection will fail.
* Set **Setup → Network → Network Control** on the receiver to **Always On**, so it
  stays reachable in standby.
* Values are pushed by the receiver; a light poll every 30 s (signal info,
  heartbeat) and a full refresh every 10 min fill in anything it doesn't push.
* Some settings only exist in certain sound modes (e.g. Cinema EQ, Neural:X); they
  keep their last reported value when not applicable.
* "Audio input signal code" is the receiver's raw code; its meanings aren't
  documented, so it's shown as-is.
