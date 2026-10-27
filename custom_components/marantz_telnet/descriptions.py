"""Describes how each protocol key is exposed as a sensor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from .const import CHANNEL_NAMES, SOURCE_NAMES, SPEAKER_GROUPS
from .protocol import db50, level

State = dict[str, str]
ValueFn = Callable[[str, State], Any]


@dataclass(frozen=True)
class SensorDesc:
    uid: str
    key: str
    name: str
    value: ValueFn = lambda raw, _s: raw
    unit: str | None = None
    diagnostic: bool = False
    enabled: bool = True
    icon: str | None = None
    numeric: bool = False
    attrs: Callable[[State], dict[str, Any]] | None = field(default=None)
    listen_prefix: str | None = None  # also refresh when keys with this prefix change


def _map(mapping: dict[str, str]) -> ValueFn:
    return lambda raw, _s: mapping.get(raw, raw)


def _int(raw: str, _s: State) -> int | None:
    raw = raw.strip()
    return int(raw) if raw.lstrip("-").isdigit() else None


def _onoff(raw: str, _s: State) -> str:
    return {"ON": "On", "OFF": "Off"}.get(raw, raw)


def _level(raw: str, _s: State) -> float | None:
    return level(raw)


def _db50(raw: str, _s: State) -> float | None:
    return db50(raw)


def source_name(code: str, state: State) -> str:
    """Friendly (possibly renamed) name for a source code."""
    return state.get(f"SSFUN:{code}") or SOURCE_NAMES.get(code, code)


def _source(raw: str, state: State) -> str:
    return source_name(raw, state)


def _lfe(raw: str, _s: State) -> int | None:
    return -int(raw) if raw.isdigit() and int(raw) else (0 if raw.isdigit() else None)


def _minutes(raw: str, _s: State) -> int | None:
    if raw == "OFF":
        return 0
    return int(raw) if raw.isdigit() else None


def _tuner(raw: str, state: State) -> str | None:
    if not raw.isdigit():
        return None
    band = state.get("TMAN_BAND", "FM")
    value = int(raw) / 100
    return f"{value:.2f} MHz" if band == "FM" else f"{value:g} kHz"


def _display_attrs(state: State) -> dict[str, Any]:
    return {f"line_{i}": state.get(f"NSE{i}") for i in range(9)}


def _speaker_attrs(state: State) -> dict[str, Any]:
    return {
        SPEAKER_GROUPS.get(k[6:], k[6:]): SPEAKER_SIZE.get(v, v) for k, v in state.items() if k.startswith("SSSPC:")
    }


def _trim_attrs(state: State) -> dict[str, Any]:
    return {
        CHANNEL_NAMES.get(k[6:], k[6:]): db50(v) for k, v in state.items() if k.startswith("SSLEV:")
    }


SPEAKER_SIZE = {"LAR": "Large", "SMA": "Small", "NON": "None", "YES": "Yes", "NO": "No",
                "1SP": "1 speaker", "2SP": "2 speakers"}
DIMMER = {"BRI": "Bright", "DIM": "Dim", "DAR": "Dark", "OFF": "Off"}
DYNVOL = {"OFF": "Off", "LIT": "Light", "MED": "Medium", "HEV": "Heavy"}
POWER = {"ON": "On", "STANDBY": "Standby", "OFF": "Off"}

D = SensorDesc
STATIC: dict[str, list[SensorDesc]] = {}


def _add(*descs: SensorDesc) -> None:
    for d in descs:
        STATIC.setdefault(d.key, []).append(d)


_add(
    D("power", "PW", "Power", _map(POWER), icon="mdi:power"),
    D("main_zone", "ZM", "Main zone power", _onoff, icon="mdi:power"),
    D("volume", "MV", "Volume", _level, numeric=True, icon="mdi:volume-high"),
    D("volume_db", "MV", "Volume (dB)", lambda r, _s: None if level(r) is None else level(r) - 80,
      unit="dB", numeric=True, icon="mdi:volume-high"),
    D("volume_max", "MVMAX", "Maximum volume", _level, numeric=True, diagnostic=True),
    D("mute", "MU", "Mute", _onoff, icon="mdi:volume-off"),
    D("input", "SI", "Input", _source, icon="mdi:import", listen_prefix="SSFUN:"),
    D("input_code", "SI", "Input code", diagnostic=True, enabled=False),
    D("video_input", "SV", "Video input", lambda r, s: "Off" if r == "OFF" else source_name(r, s), icon="mdi:video-input-hdmi"),
    D("audio_input_mode", "SD", "Audio input mode", icon="mdi:audio-input-rca"),
    D("digital_input_mode", "DC", "Digital input mode", icon="mdi:audio-input-stereo-minijack"),
    D("sound_mode", "MS", "Sound mode", icon="mdi:surround-sound"),
    D("sound_mode_category", "SSSMG", "Sound mode category", _map({"MOV": "Movie", "MUS": "Music", "GAM": "Game", "PUR": "Pure"}), icon="mdi:surround-sound"),
    D("smart_select", "MSSMART", "Smart select", diagnostic=True),
    D("sleep", "SLP", "Sleep timer", _minutes, unit="min", numeric=True, icon="mdi:timer-sand"),
    D("auto_standby", "STBY", "Auto standby", _map({"OFF": "Off", "15M": "15 min", "30M": "30 min", "60M": "60 min"}), icon="mdi:timer-off"),
    D("eco", "ECO", "ECO mode", _map({"ON": "On", "AUTO": "Auto", "OFF": "Off"}), icon="mdi:leaf"),
    D("dimmer", "DIM", "Display dimmer", _map(DIMMER), icon="mdi:brightness-6"),
    # Audio
    D("tone_control", "PS:TONE_CTRL", "Tone control", _onoff, icon="mdi:tune"),
    D("bass", "PS:BAS", "Bass", _db50, unit="dB", numeric=True, icon="mdi:tune"),
    D("treble", "PS:TRE", "Treble", _db50, unit="dB", numeric=True, icon="mdi:tune"),
    D("drc", "PS:DRC", "Dynamic compression", _map({"AUTO": "Auto", "LOW": "Low", "MID": "Medium", "HI": "High", "OFF": "Off"}), icon="mdi:arrow-collapse-vertical"),
    D("lfe", "PS:LFE", "LFE level", _lfe, unit="dB", numeric=True, icon="mdi:speaker"),
    D("multeq", "PS:MULTEQ", "MultEQ", _map({"AUDYSSEY": "Reference", "BYP.LR": "Bypass L/R", "FLAT": "Flat", "MANUAL": "Manual", "OFF": "Off"}), icon="mdi:equalizer"),
    D("dynamic_eq", "PS:DYNEQ", "Dynamic EQ", _onoff, icon="mdi:equalizer"),
    D("reference_level", "PS:REFLEV", "Reference level offset", _int, unit="dB", numeric=True),
    D("dynamic_volume", "PS:DYNVOL", "Dynamic volume", _map(DYNVOL), icon="mdi:volume-equal"),
    D("cinema_eq", "PS:CINEMA_EQ", "Cinema EQ", _onoff, icon="mdi:movie-open"),
    D("dialog_level_adjust", "PS:DIL_SW", "Dialog level adjust", _onoff, icon="mdi:account-voice"),
    D("dialog_level", "PS:DIL", "Dialog level", _db50, unit="dB", numeric=True, icon="mdi:account-voice"),
    D("subwoofer", "PS:SWR", "Subwoofer output", _onoff, icon="mdi:speaker"),
    D("subwoofer_level_adjust", "PS:SWL_SW", "Subwoofer level adjust", _onoff, icon="mdi:speaker"),
    D("subwoofer_level", "PS:SWL", "Subwoofer level", _db50, unit="dB", numeric=True, icon="mdi:speaker"),
    D("audio_delay", "PS:DELAY", "Audio delay", _int, unit="ms", numeric=True, icon="mdi:timer-outline"),
    D("effect_delay", "PS:DEL", "Effect delay", _int, unit="ms", numeric=True, diagnostic=True),
    D("headphone_eq", "PS:HEQ", "Headphone EQ", _onoff, icon="mdi:headphones"),
    D("effect_level", "PS:EFF", "Effect level", _int, numeric=True, diagnostic=True),
    D("room_size", "PS:RSZ", "Room size", diagnostic=True),
    D("graphic_eq", "PS:GEQ", "Graphic EQ", _onoff, icon="mdi:equalizer"),
    D("neural_x", "PS:NEURAL", "Neural:X", _onoff, icon="mdi:surround-sound"),
    D("loudness_management", "PS:LOM", "Loudness management", _onoff),
    D("center_spread", "PS:CES", "Center spread", _onoff),
    D("mdax", "PS:MDAX", "M-DAX", _map({"OFF": "Off", "LOW": "Low", "MID": "Medium", "HI": "High"}), icon="mdi:music-note-plus"),
    D("audyssey_lfc", "PS:LFC", "Audyssey LFC", _onoff),
    D("containment_amount", "PS:CNTAMT", "Containment amount", _int, numeric=True),
    D("dialog_enhancer", "PS:DEH", "Dialog enhancer"),
    D("bass_sync", "PS:BSC", "Bass sync"),
    D("audio_restorer", "PS:RSTR", "Audio restorer"),
    # Video
    D("aspect", "VS:ASP", "Aspect ratio", _map({"NRM": "Normal", "FUL": "Full"}), icon="mdi:aspect-ratio"),
    D("hdmi_monitor", "VS:MONI", "HDMI monitor out", icon="mdi:monitor"),
    D("output_resolution", "VS:SC", "Output resolution", icon="mdi:monitor"),
    D("hdmi_resolution", "VS:SCH", "HDMI output resolution", icon="mdi:monitor"),
    D("hdmi_audio_out", "VS:AUDIO", "HDMI audio output", _map({"AMP": "AVR", "TV": "TV"}), icon="mdi:television-speaker"),
    D("video_processing", "VS:VPM", "Video processing mode", _map({"AUTO": "Auto", "GAME": "Game", "MOVI": "Movie", "BYP": "Bypass"}), icon="mdi:video"),
    D("vertical_stretch", "VS:VST", "Vertical stretch", _onoff, diagnostic=True),
    D("picture_mode", "PV", "Picture mode", diagnostic=True),
    # Signal information
    D("audio_signal", "SSINFAIS:SIG", "Audio input signal code", icon="mdi:waveform"),
    D("sample_rate", "SSINFAIS:FSV", "Audio sample rate", icon="mdi:waveform"),
    D("channel_format", "SSINFAIS:FOR", "Audio channel format", icon="mdi:surround-sound"),
    D("input_resolution", "SSINFSIGRES:I", "Input video resolution", icon="mdi:video-input-hdmi"),
    D("output_video_resolution", "SSINFSIGRES:O", "Output video resolution", icon="mdi:monitor"),
    # Zone 2
    D("z2_power", "Z2PW", "Zone 2 power", _onoff, icon="mdi:power"),
    D("z2_volume", "Z2MV", "Zone 2 volume", _level, numeric=True, icon="mdi:volume-high"),
    D("z2_mute", "Z2MU", "Zone 2 mute", _onoff, icon="mdi:volume-off"),
    D("z2_input", "Z2SI", "Zone 2 input", _source, icon="mdi:import"),
    D("z2_sleep", "Z2SLP", "Zone 2 sleep timer", _minutes, unit="min", numeric=True),
    D("z2_standby", "Z2STBY", "Zone 2 auto standby", _map({"OFF": "Off", "2H": "2 h", "4H": "4 h", "8H": "8 h"})),
    D("z2_bass", "Z2PSBAS", "Zone 2 bass", _db50, unit="dB", numeric=True),
    D("z2_treble", "Z2PSTRE", "Zone 2 treble", _db50, unit="dB", numeric=True),
    D("z2_hpf", "Z2HPF", "Zone 2 high-pass filter", _onoff, diagnostic=True),
    # Tuner
    D("tuner_frequency", "TFAN", "Tuner frequency", _tuner, icon="mdi:radio", listen_prefix="TMAN_BAND"),
    D("tuner_preset", "TPAN", "Tuner preset", _int, numeric=True, icon="mdi:radio"),
    D("tuner_band", "TMAN_BAND", "Tuner band", icon="mdi:radio"),
    D("tuner_mode", "TMAN_MODE", "Tuner tuning mode", icon="mdi:radio", diagnostic=True),
    # Display / online music
    D("display", "NSE1", "Display", attrs=_display_attrs, listen_prefix="NSE", icon="mdi:text-box-outline"),
    # Misc / system
    D("trigger_1", "TR:1", "Trigger 1", _onoff, diagnostic=True),
    D("trigger_2", "TR:2", "Trigger 2", _onoff, diagnostic=True),
    D("setup_menu", "MNMEN", "Setup menu open", _onoff, diagnostic=True),
    D("all_zone_stereo", "MNZST", "All zone stereo", _onoff),
    D("friendly_name", "NSFRN", "Friendly name", diagnostic=True),
    D("model", "SYMO", "Model", diagnostic=True),
    D("firmware", "SSINFFRM:AVR", "Firmware", diagnostic=True),
    D("dts_firmware", "SSINFFRM:DTS", "DTS firmware", diagnostic=True),
    D("language", "SSLAN", "Menu language", diagnostic=True),
    D("setup_lock", "SSLOC", "Setup lock", _onoff, diagnostic=True),
    D("amp_assign", "SSPAA:MOD", "Power amp assign", diagnostic=True),
    D("lip_sync", "SSALS:SET", "Auto lip sync", _onoff, diagnostic=True),
    D("lip_sync_dsp", "SSALS:DSP", "Lip sync (DSP)", _onoff, diagnostic=True, enabled=False),
    D("lip_sync_value", "SSALS:VAL", "Lip sync delay", _int, unit="ms", numeric=True, diagnostic=True),
    D("hdmi_control", "SSHOS:CON", "HDMI control", _onoff, diagnostic=True),
    D("hdmi_power_off_control", "SSHOS:CONPOF", "HDMI power off control", diagnostic=True),
    D("hdmi_arc", "SSHOS:CONARC", "HDMI ARC", _onoff, diagnostic=True),
    D("hdmi_power_saving", "SSHOS:CONPSV", "HDMI power saving", _onoff, diagnostic=True),
    D("hdmi_standby_source", "SSHOS:CONSTS", "HDMI standby source", diagnostic=True),
    D("speaker_config", "SSSPC:FRO", "Speaker configuration",
      lambda _r, s: sum(1 for k, v in s.items() if k.startswith("SSSPC:") and k != "SSSPC:SBK_COUNT" and v not in ("NON", "NO")),
      attrs=_speaker_attrs, listen_prefix="SSSPC:", diagnostic=True, icon="mdi:speaker-multiple"),
    D("speaker_trims", "SSLEV:FL", "Speaker trims", lambda r, _s: db50(r), unit="dB",
      attrs=_trim_attrs, listen_prefix="SSLEV:", diagnostic=True, enabled=False, icon="mdi:speaker-multiple"),
    D("last_message", "LAST", "Last message", diagnostic=True, enabled=False),
    D("unrecognized", "UNKNOWN", "Last unrecognized message", diagnostic=True, enabled=False),
)


# Sensors enabled when the integration is added; everything else is created
# disabled and can be enabled per entity in Home Assistant.
DEFAULT_SENSORS = {
    "input",
    "sound_mode",
    "volume_db",
    "audio_input_mode",
    "sample_rate",
    "channel_format",
    "input_resolution",
    "display",
    "firmware",
}


def describe(key: str) -> list[SensorDesc]:
    """Return the sensors to create for a protocol key."""
    descs = list(STATIC.get(key, []))
    fam, _, sub = key.partition(":")

    if key.startswith("NSE") and key[3:].isdigit():
        descs.append(D(f"display_line_{key[3:]}", key, f"Display line {key[3:]}", enabled=False))
    elif fam in ("CV", "Z2CV"):
        prefix = "Zone 2 channel level" if fam == "Z2CV" else "Channel level"
        descs.append(D(f"{fam.lower()}_{sub.lower()}", key,
                       f"{prefix} {CHANNEL_NAMES.get(sub, sub)}", _db50, unit="dB",
                       numeric=True, icon="mdi:speaker"))
    elif fam == "SSLEV":
        descs.append(D(f"trim_{sub.lower()}", key, f"Speaker trim {CHANNEL_NAMES.get(sub, sub)}",
                       _db50, unit="dB", numeric=True, diagnostic=True))
    elif fam == "SSSPC":
        descs.append(D(f"speaker_{sub.lower()}", key,
                       f"Speaker {SPEAKER_GROUPS.get(sub, sub)}", _map(SPEAKER_SIZE),
                       diagnostic=True))
    elif fam == "SSFUN":
        descs.append(D(f"source_name_{sub.lower()}", key, f"Source name {sub}",
                       diagnostic=True, enabled=False))
    elif fam == "SSSOD":
        descs.append(D(f"source_used_{sub.lower()}", key, f"Source {sub} in use",
                       _map({"USE": "Yes", "DEL": "No"}), diagnostic=True, enabled=False))
    elif not descs:
        if fam == "SSINFFRM":
            descs.append(D(f"firmware_{sub.lower()}", key, f"Firmware {sub}", diagnostic=True))
        elif fam == "SSHOS":
            descs.append(D(f"hdmi_setting_{sub.lower()}", key, f"HDMI setting {sub}", diagnostic=True))
        else:
            slug = "".join(c if c.isalnum() else "_" for c in key.lower())
            descs.append(D(f"raw_{slug}", key, f"Raw {key}", diagnostic=True, enabled=False))
    return [replace(d, enabled=d.uid in DEFAULT_SENSORS) for d in descs]
