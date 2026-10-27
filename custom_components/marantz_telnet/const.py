"""Constants for the Marantz/Denon telnet integration."""

DOMAIN = "marantz_telnet"
DEFAULT_PORT = 23

FAST_POLL_INTERVAL = 30  # seconds: signal info, power, volume (also a heartbeat)
FULL_POLL_INTERVAL = 600  # seconds: everything

# Queried first so the device can be named/identified quickly.
IDENTITY_QUERIES = ["PW?", "SYMO", "NSFRN ?", "SSINFFRM ?", "SSFUN ?", "SSSOD ?"]

STATE_QUERIES = [
    "ZM?", "MV?", "MU?", "SI?", "SV?", "SD?", "DC?", "MS?", "MSSMART ?", "SLP?", "STBY?",
    "ECO?", "CV?", "DIM ?", "PSTONE CTRL ?", "PSBAS ?", "PSTRE ?", "PSDRC ?", "PSLFE ?",
    "PSMULTEQ: ?", "PSDYNEQ ?", "PSREFLEV ?", "PSDYNVOL ?", "PSCINEMA EQ. ?", "PSDIL ?",
    "PSSWR ?", "PSSWL ?", "PSDELAY ?", "PSDEL ?", "PSHEQ ?", "PSEFF ?", "PSRSZ ?",
    "PSGEQ ?", "PSNEURAL ?", "PSLOM ?", "PSCES ?", "PSMDAX ?", "PSLFC ?", "PSCNTAMT ?",
    "PSDEH ?", "PSBSC ?", "PSRSTR ?", "PSPAN ?", "PSDIM ?", "PSCEN ?", "PSCEI ?",
    "PSCEG ?", "VSASP ?", "VSMONI ?", "VSSC ?", "VSSCH ?", "VSAUDIO ?", "VSVPM ?",
    "VSVST ?", "Z2?", "Z2MU?", "Z2CV?", "Z2SLP?", "Z2STBY?", "Z2HPF?", "Z2PSBAS ?",
    "Z2PSTRE ?", "TFAN?", "TPAN?", "TMAN?", "NSE", "TR?", "PV?", "MNMEN?", "MNZST?",
    "SSSPC ?", "SSLEV ?", "SSLAN ?", "SSALS ?", "SSHOS ?", "SSPAA ?", "SSLOC ?",
    "SSSMG ?",
]

SIGNAL_QUERIES = [
    "SSINFAISSIG ?", "SSINFAISFSV ?", "SSINFAISFOR ?", "SSINFSIGRES ?", "SD?", "DC?",
]

FAST_QUERIES = ["PW?", "ZM?", "MV?", "MU?", "SI?", "MS?", "Z2?", *SIGNAL_QUERIES]

# Re-queried after the input or sound mode changes (many values are mode dependent).
MODE_QUERIES = [
    *SIGNAL_QUERIES, "CV?", "PSDRC ?", "PSDYNEQ ?", "PSDYNVOL ?", "PSMULTEQ: ?",
    "PSCINEMA EQ. ?", "PSLFE ?", "PSDIL ?", "PSSWL ?", "PSNEURAL ?", "PSLOM ?",
    "PSCES ?", "PSMDAX ?", "PSEFF ?", "PSDEL ?", "PSRSZ ?", "SSSMG ?",
]

NET_SOURCES = {
    "NET", "BT", "USB/IPOD", "USB", "IPD", "IRADIO", "SERVER", "FAVORITES", "SPOTIFY",
    "PANDORA", "SIRIUSXM", "FLICKR", "IRP", "FVP", "MPLAY",
}

SOURCE_NAMES = {
    "PHONO": "Phono", "CD": "CD", "DVD": "DVD", "BD": "Blu-ray", "TV": "TV Audio",
    "SAT/CBL": "CBL/SAT", "SAT": "SAT", "MPLAY": "Media Player", "GAME": "Game",
    "TUNER": "Tuner", "AUX1": "AUX1", "AUX2": "AUX2", "NET": "Online Music",
    "BT": "Bluetooth", "USB/IPOD": "iPod/USB", "USB": "USB", "IPD": "iPod",
    "IRADIO": "Internet Radio", "SERVER": "Media Server", "FAVORITES": "Favorites",
    "SIRIUSXM": "SiriusXM", "PANDORA": "Pandora", "SPOTIFY": "Spotify",
    "SOURCE": "Main zone source",
}

SOUND_MODES = [
    "DIRECT", "PURE DIRECT", "STEREO", "AUTO", "MOVIE", "MUSIC", "GAME",
    "DOLBY DIGITAL", "DTS SURROUND", "MCH STEREO", "VIRTUAL",
]

CHANNEL_NAMES = {
    "FL": "Front left", "FR": "Front right", "C": "Center", "SW": "Subwoofer",
    "SW2": "Subwoofer 2", "SL": "Surround left", "SR": "Surround right",
    "SBL": "Surround back left", "SBR": "Surround back right", "SB": "Surround back",
    "FHL": "Front height left", "FHR": "Front height right", "FWL": "Front wide left",
    "FWR": "Front wide right", "TFL": "Top front left", "TFR": "Top front right",
    "TML": "Top middle left", "TMR": "Top middle right", "TRL": "Top rear left",
    "TRR": "Top rear right", "RHL": "Rear height left", "RHR": "Rear height right",
    "FDL": "Front Dolby left", "FDR": "Front Dolby right", "SDL": "Surround Dolby left",
    "SDR": "Surround Dolby right", "BDL": "Back Dolby left", "BDR": "Back Dolby right",
    "SHL": "Surround height left", "SHR": "Surround height right", "TS": "Top surround",
    "CH": "Center height",
}

SPEAKER_GROUPS = {
    "FRO": "Front", "CEN": "Center", "SUA": "Surround", "SBK": "Surround back",
    "SBK_COUNT": "Surround back count", "FRH": "Front height", "TFR": "Top front",
    "TPM": "Top middle", "FRD": "Front Dolby", "SUD": "Surround Dolby",
    "SWF": "Subwoofer", "FRW": "Front wide", "RHE": "Rear height", "BKD": "Back Dolby",
}
