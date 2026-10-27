"""Definitions of the writable settings (selects, switches, numbers)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .const import CHANNEL_NAMES
from .protocol import db50, encode_level, level


@dataclass(frozen=True)
class SelectDesc:
    uid: str
    key: str
    name: str
    options: dict[str, str]  # protocol value -> label
    command: str  # format string with {v}
    icon: str | None = None


@dataclass(frozen=True)
class SwitchDesc:
    uid: str
    key: str
    name: str
    command: str  # format string with {v} = ON/OFF
    icon: str | None = None


@dataclass(frozen=True)
class NumberDesc:
    uid: str
    key: str
    name: str
    minimum: float
    maximum: float
    step: float
    decode: Callable[[str], float | None]
    encode: Callable[[float], str]  # full command
    unit: str | None = None
    icon: str | None = None


# Controls enabled when the integration is added; the rest start disabled.
DEFAULT_CONTROLS = {
    "multeq", "dynamic_volume", "dynamic_eq", "cinema_eq", "tone_control",
    "bass", "treble", "dialog_level", "subwoofer_level", "sleep", "dimmer", "eco",
}

SELECTS = [
    SelectDesc("eco", "ECO", "ECO mode", {"ON": "On", "AUTO": "Auto", "OFF": "Off"}, "ECO{v}", "mdi:leaf"),
    SelectDesc("dimmer", "DIM", "Display dimmer",
               {"BRI": "Bright", "DIM": "Dim", "DAR": "Dark", "OFF": "Off"}, "DIM {v}", "mdi:brightness-6"),
    SelectDesc("digital_input_mode", "DC", "Digital input mode",
               {"AUTO": "Auto", "PCM": "PCM", "DTS": "DTS"}, "DC{v}"),
    SelectDesc("audio_input_mode", "SD", "Audio input mode",
               {"AUTO": "Auto", "HDMI": "HDMI", "DIGITAL": "Digital", "ANALOG": "Analog",
                "NO": "No input"}, "SD{v}"),
    SelectDesc("multeq", "PS:MULTEQ", "MultEQ",
               {"AUDYSSEY": "Reference", "BYP.LR": "Bypass L/R", "FLAT": "Flat",
                "MANUAL": "Manual", "OFF": "Off"}, "PSMULTEQ:{v}", "mdi:equalizer"),
    SelectDesc("dynamic_volume", "PS:DYNVOL", "Dynamic volume",
               {"OFF": "Off", "LIT": "Light", "MED": "Medium", "HEV": "Heavy"}, "PSDYNVOL {v}",
               "mdi:volume-equal"),
    SelectDesc("drc", "PS:DRC", "Dynamic compression",
               {"AUTO": "Auto", "LOW": "Low", "MID": "Medium", "HI": "High", "OFF": "Off"},
               "PSDRC {v}", "mdi:arrow-collapse-vertical"),
    SelectDesc("reference_level", "PS:REFLEV", "Reference level offset",
               {"0": "0 dB", "5": "5 dB", "10": "10 dB", "15": "15 dB"}, "PSREFLEV {v}"),
    SelectDesc("video_processing", "VS:VPM", "Video processing mode",
               {"AUTO": "Auto", "GAME": "Game", "MOVI": "Movie", "BYP": "Bypass"}, "VSVPM{v}", "mdi:video"),
    SelectDesc("hdmi_audio_out", "VS:AUDIO", "HDMI audio output", {"AMP": "AVR", "TV": "TV"},
               "VSAUDIO {v}", "mdi:television-speaker"),
    SelectDesc("aspect", "VS:ASP", "Aspect ratio", {"NRM": "Normal", "FUL": "Full"}, "VSASP{v}",
               "mdi:aspect-ratio"),
    SelectDesc("auto_standby", "STBY", "Auto standby",
               {"OFF": "Off", "15M": "15 min", "30M": "30 min", "60M": "60 min"}, "STBY{v}",
               "mdi:timer-off"),
]

SWITCHES = [
    SwitchDesc("dynamic_eq", "PS:DYNEQ", "Dynamic EQ", "PSDYNEQ {v}", "mdi:equalizer"),
    SwitchDesc("cinema_eq", "PS:CINEMA_EQ", "Cinema EQ", "PSCINEMA EQ.{v}", "mdi:movie-open"),
    SwitchDesc("tone_control", "PS:TONE_CTRL", "Tone control", "PSTONE CTRL {v}", "mdi:tune"),
    SwitchDesc("loudness_management", "PS:LOM", "Loudness management", "PSLOM {v}"),
    SwitchDesc("dialog_level_adjust", "PS:DIL_SW", "Dialog level adjust", "PSDIL {v}", "mdi:account-voice"),
    SwitchDesc("subwoofer_level_adjust", "PS:SWL_SW", "Subwoofer level adjust", "PSSWL {v}", "mdi:speaker"),
    SwitchDesc("subwoofer", "PS:SWR", "Subwoofer output", "PSSWR {v}", "mdi:speaker"),
    SwitchDesc("graphic_eq", "PS:GEQ", "Graphic EQ", "PSGEQ {v}", "mdi:equalizer"),
    SwitchDesc("headphone_eq", "PS:HEQ", "Headphone EQ", "PSHEQ {v}", "mdi:headphones"),
    SwitchDesc("neural_x", "PS:NEURAL", "Neural:X", "PSNEURAL {v}", "mdi:surround-sound"),
    SwitchDesc("center_spread", "PS:CES", "Center spread", "PSCES {v}"),
    SwitchDesc("audyssey_lfc", "PS:LFC", "Audyssey LFC", "PSLFC {v}"),
    SwitchDesc("trigger_1", "TR:1", "Trigger 1", "TR1 {v}", "mdi:electric-switch"),
    SwitchDesc("trigger_2", "TR:2", "Trigger 2", "TR2 {v}", "mdi:electric-switch"),
    SwitchDesc("all_zone_stereo", "MNZST", "All zone stereo", "MNZST {v}", "mdi:speaker-multiple"),
]


def _db50_cmd(prefix: str) -> Callable[[float], str]:
    return lambda v: f"{prefix}{encode_level(v + 50)}"


def _sleep_cmd(prefix: str) -> Callable[[float], str]:
    return lambda v: f"{prefix}OFF" if v <= 0 else f"{prefix}{int(v):03d}"


def _sleep_decode(raw: str) -> float | None:
    return 0 if raw == "OFF" else (float(raw) if raw.isdigit() else None)


def _int_decode(raw: str) -> float | None:
    return float(raw) if raw.isdigit() else None


NUMBERS = [
    NumberDesc("bass", "PS:BAS", "Bass", -6, 6, 1, db50, _db50_cmd("PSBAS "), "dB", "mdi:tune"),
    NumberDesc("treble", "PS:TRE", "Treble", -6, 6, 1, db50, _db50_cmd("PSTRE "), "dB", "mdi:tune"),
    NumberDesc("lfe", "PS:LFE", "LFE level", -10, 0, 1,
               lambda r: -float(r) if r.isdigit() and int(r) else (0.0 if r.isdigit() else None),
               lambda v: f"PSLFE {int(-v):02d}", "dB", "mdi:speaker"),
    NumberDesc("dialog_level", "PS:DIL", "Dialog level", -12, 12, 0.5, db50, _db50_cmd("PSDIL "),
               "dB", "mdi:account-voice"),
    NumberDesc("subwoofer_level", "PS:SWL", "Subwoofer level", -12, 12, 0.5, db50,
               _db50_cmd("PSSWL "), "dB", "mdi:speaker"),
    NumberDesc("audio_delay", "PS:DELAY", "Audio delay", 0, 200, 1, _int_decode,
               lambda v: f"PSDELAY {int(v):03d}", "ms", "mdi:timer-outline"),
    NumberDesc("sleep", "SLP", "Sleep timer", 0, 120, 10, _sleep_decode, _sleep_cmd("SLP"),
               "min", "mdi:timer-sand"),
    NumberDesc("z2_sleep", "Z2SLP", "Zone 2 sleep timer", 0, 120, 10, _sleep_decode,
               _sleep_cmd("Z2SLP"), "min", "mdi:timer-sand"),
    NumberDesc("tuner_preset", "TPAN", "Tuner preset", 1, 56, 1, _int_decode,
               lambda v: f"TPAN{int(v):02d}", None, "mdi:radio"),
    NumberDesc("z2_bass", "Z2PSBAS", "Zone 2 bass", -10, 10, 1, db50, _db50_cmd("Z2PSBAS "), "dB"),
    NumberDesc("z2_treble", "Z2PSTRE", "Zone 2 treble", -10, 10, 1, db50, _db50_cmd("Z2PSTRE "), "dB"),
]


def channel_number(key: str) -> NumberDesc | None:
    """Channel level controls for CV:<ch> / Z2CV:<ch> keys."""
    fam, _, ch = key.partition(":")
    if fam not in ("CV", "Z2CV") or not ch:
        return None
    prefix = "Zone 2 channel level" if fam == "Z2CV" else "Channel level"
    return NumberDesc(
        f"{fam.lower()}_{ch.lower()}", key, f"{prefix} {CHANNEL_NAMES.get(ch, ch)}",
        -12, 12, 0.5, db50, _db50_cmd(f"{fam}{ch} "), "dB", "mdi:speaker",
    )


__all__ = ["SELECTS", "SWITCHES", "NUMBERS", "channel_number", "level"]
