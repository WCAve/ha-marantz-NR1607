"""Parsing and encoding helpers for the Denon/Marantz telnet protocol.

Every line the receiver sends is turned into a (key, value) pair. Keys are
stable identifiers used by the entities, e.g. ``MV``, ``PS:BAS``, ``CV:FL``,
``SSLEV:SW`` or ``SSINFAIS:FSV``.
"""

from __future__ import annotations

import re

PS_PARAMS = sorted(
    [
        "CINEMA EQ.", "TONE CTRL", "MULTEQ:", "DYNEQ", "REFLEV", "DYNVOL", "LFC",
        "CNTAMT", "DIL", "DEH", "BSC", "SWR", "DELAY", "RSTR", "FH:", "SP:", "HEQ",
        "MODE:", "PAN", "DIM", "CEN", "CEI", "CEG", "SWL", "AUROPR", "AUROST", "DSX",
        "EFF", "DEL", "AFD", "RSZ", "GEQ", "NEURAL", "LOM", "BAL", "STW", "STH", "PHG",
        "CES", "MDAX", "DRC", "LFE", "BAS", "TRE", "SPV",
    ],
    key=len,
    reverse=True,
)
VS_PARAMS = sorted(["MONI", "AUDIO", "ASP", "SCH", "VPM", "VST", "SC"], key=len, reverse=True)
SS_FAMILIES = sorted(
    ["SSINFFRM", "SSINFAIS", "SSINFSIGRES", "SSLEV", "SSSPC", "SSFUN", "SSSOD", "SSHOS", "SSALS", "SSPAA"],
    key=len,
    reverse=True,
)
SIMPLE = sorted(
    [
        "PW", "ZM", "MU", "SI", "SV", "SD", "DC", "SLP", "STBY", "ECO", "DIM", "TFAN",
        "TPAN", "PV", "MNMEN", "MNZST", "NSFRN", "SYMO", "SSSMG", "SSLAN", "SSLOC",
    ],
    key=len,
    reverse=True,
)
Z2_SUBS = ["PSBAS", "PSTRE", "QUICK", "SMART", "STBY", "SLP", "HPF", "HDA", "MU"]

_CV_RE = re.compile(r"^(Z2)?CV([A-Z0-9]+) (\d+)$")
_TR_RE = re.compile(r"^TR(\d) ?(ON|OFF)$")


def parse_line(line: str) -> tuple[str, str] | None:
    """Parse one line from the receiver into (key, value)."""
    line = line.strip("\r\n\x00").strip()
    if not line:
        return None

    # Online-music / display lines. NSA duplicates NSE, NSH are preset names.
    if line.startswith("NSE") and len(line) > 3 and line[3].isdigit():
        text = "".join(ch for ch in line[4:] if ch >= " ")
        return f"NSE{line[3]}", text.strip()
    if line.startswith(("NSA", "NSH")):
        return None
    if line in ("CVEND", "Z2CVEND"):
        return None

    if m := _CV_RE.match(line):
        prefix = "Z2CV" if m.group(1) else "CV"
        return f"{prefix}:{m.group(2)}", m.group(3)

    for fam in SS_FAMILIES:
        if line.startswith(fam):
            rest = line[len(fam):].lstrip()
            sub, _, val = rest.partition(" ")
            val = val.strip()
            if fam == "SSSPC" and sub == "SBK" and val.endswith("SP"):
                sub = "SBK_COUNT"
            if not sub:
                return fam, val
            return f"{fam}:{sub}", val

    if line.startswith("Z2"):
        rest = line[2:]
        if rest in ("ON", "OFF"):
            return "Z2PW", rest
        if rest.isdigit():
            return "Z2MV", rest
        for sub in Z2_SUBS:
            if rest.startswith(sub):
                return f"Z2{sub}", rest[len(sub):].strip()
        return "Z2SI", rest

    if line.startswith("PS"):
        rest = line[2:]
        for p in PS_PARAMS:
            if rest.startswith(p):
                val = rest[len(p):].strip()
                name = p.rstrip(":. ").replace(" ", "_").replace(".", "")
                if name in ("DIL", "SWL") and val in ("ON", "OFF"):
                    name += "_SW"
                return f"PS:{name}", val
        name, _, val = rest.partition(" ")
        return f"PS:{name}", val.strip()

    if line.startswith("VS"):
        rest = line[2:]
        for p in VS_PARAMS:
            if rest.startswith(p):
                return f"VS:{p}", rest[len(p):].strip()
        return f"VS:{rest}", ""

    if line.startswith("MV"):
        if line.startswith("MVMAX"):
            return "MVMAX", line[5:].strip()
        return "MV", line[2:].strip()

    if line.startswith("MS"):
        for sub in ("SMART", "QUICK"):
            if line.startswith("MS" + sub):
                return f"MS{sub}", line[2 + len(sub):].strip()
        return "MS", line[2:].strip()

    if line.startswith("TMAN"):
        val = line[4:].strip()
        return ("TMAN_MODE" if val in ("AUTO", "MANUAL") else "TMAN_BAND"), val

    if m := _TR_RE.match(line):
        return f"TR:{m.group(1)}", m.group(2)

    for p in SIMPLE:
        if line.startswith(p):
            return p, line[len(p):].strip()

    return "UNKNOWN", line


def level(raw: str | None) -> float | None:
    """Decode a 2/3 digit level: '52' -> 52.0, '525' -> 52.5."""
    if raw is None:
        return None
    raw = raw.strip()
    if not raw.isdigit():
        return None
    return int(raw) / 10 if len(raw) == 3 else float(int(raw))


def db50(raw: str | None) -> float | None:
    """Decode a level where 50 means 0 dB."""
    val = level(raw)
    return None if val is None else val - 50


def encode_level(value: float) -> str:
    """Encode a level (0..99, 0.5 steps) into '52' / '525' form."""
    value = round(value * 2) / 2
    if value != int(value):
        return f"{int(round(value * 10)):03d}"
    return f"{int(value):02d}"
