"""Media players for the main zone and zone 2."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import AVRClient
from .const import NET_SOURCES, SOUND_MODES
from .descriptions import source_name
from .entity import AVREntity, setup_dynamic
from .protocol import encode_level, level

FEATURES = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    client: AVRClient = entry.runtime_data
    async_add_entities([AVRMediaPlayer(entry, client, zone2=False)])

    def factory(key: str) -> list:
        return [AVRMediaPlayer(entry, client, zone2=True)] if key == "Z2PW" else []

    setup_dynamic(entry, client, async_add_entities, factory)


class AVRMediaPlayer(AVREntity, MediaPlayerEntity):
    """Main zone or zone 2."""

    def __init__(self, entry: ConfigEntry, client: AVRClient, zone2: bool) -> None:
        self._z2 = zone2
        if zone2:
            keys = ["Z2PW", "Z2MV", "Z2MU", "Z2SI"]
        else:
            keys = ["ZM", "PW", "MV", "MU", "SI", "MS", "MVMAX", "NSE1", "NSE2", "NSE4"]
        super().__init__(
            entry, client, "zone2" if zone2 else "main", keys, None if zone2 else "SSSOD:"
        )
        self._attr_name = "Zone 2" if zone2 else None
        self._attr_supported_features = FEATURES | (
            MediaPlayerEntityFeature(0) if zone2 else MediaPlayerEntityFeature.SELECT_SOUND_MODE
        )
        self._attr_sound_mode_list = None if zone2 else SOUND_MODES

    @property
    def available(self) -> bool:
        return self._client.connected and self._keys[0] in self._client.state

    # ------------------------------------------------------------------ state
    @property
    def state(self) -> MediaPlayerState | None:
        value = self.raw(self._keys[0])
        if value is None:
            return None
        return MediaPlayerState.ON if value == "ON" else MediaPlayerState.OFF

    @property
    def _max(self) -> float:
        return level(self.raw("MVMAX")) or 98.0

    @property
    def volume_level(self) -> float | None:
        vol = level(self.raw("Z2MV" if self._z2 else "MV"))
        return None if vol is None else max(0.0, min(1.0, vol / 98.0))

    @property
    def is_volume_muted(self) -> bool | None:
        mute = self.raw("Z2MU" if self._z2 else "MU")
        return None if mute is None else mute == "ON"

    @property
    def source_list(self) -> list[str]:
        state = self._client.state
        codes = [k[6:] for k, v in state.items() if k.startswith("SSSOD:") and v == "USE"]
        if not codes:
            codes = [k[6:] for k in state if k.startswith("SSFUN:")]
        current = self.raw("SI")
        if current and current not in codes:
            codes.append(current)
        names = [source_name(c, state) for c in codes]
        if self._z2:
            names.insert(0, source_name("SOURCE", state))
        return names

    def _code_for(self, name: str) -> str:
        state = self._client.state
        candidates = {k[6:] for k in state if k.startswith(("SSSOD:", "SSFUN:"))}
        candidates |= {"SOURCE", self.raw("SI") or ""}
        for code in candidates:
            if code and source_name(code, state) == name:
                return code
        return name.upper()

    @property
    def source(self) -> str | None:
        code = self.raw("Z2SI" if self._z2 else "SI")
        return None if code is None else source_name(code, self._client.state)

    @property
    def sound_mode(self) -> str | None:
        return None if self._z2 else self.raw("MS")

    @property
    def media_title(self) -> str | None:
        if self._z2 or self.raw("SI") not in NET_SOURCES:
            return None
        return self.raw("NSE1") or None

    @property
    def media_artist(self) -> str | None:
        if self._z2 or self.raw("SI") not in NET_SOURCES:
            return None
        return self.raw("NSE2") or None

    @property
    def media_album_name(self) -> str | None:
        if self._z2 or self.raw("SI") not in NET_SOURCES:
            return None
        return self.raw("NSE4") or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        vol = level(self.raw("Z2MV" if self._z2 else "MV"))
        attrs: dict[str, Any] = {"volume_raw": vol}
        if vol is not None:
            attrs["volume_db"] = vol - 80
        if not self._z2:
            attrs["power"] = self.raw("PW")
        return attrs

    # ------------------------------------------------------------------ commands
    async def async_turn_on(self) -> None:
        self.send("Z2ON" if self._z2 else "ZMON")

    async def async_turn_off(self) -> None:
        self.send("Z2OFF" if self._z2 else "ZMOFF")

    async def async_set_volume_level(self, volume: float) -> None:
        value = max(0.0, min(self._max, volume * 98.0))
        if self._z2:
            self.send(f"Z2{int(round(value)):02d}")
        else:
            self.send(f"MV{encode_level(value)}")

    async def async_volume_up(self) -> None:
        self.send("Z2UP" if self._z2 else "MVUP")

    async def async_volume_down(self) -> None:
        self.send("Z2DOWN" if self._z2 else "MVDOWN")

    async def async_mute_volume(self, mute: bool) -> None:
        self.send(("Z2MU" if self._z2 else "MU") + ("ON" if mute else "OFF"))

    async def async_select_source(self, source: str) -> None:
        code = self._code_for(source)
        self.send(f"Z2{code}" if self._z2 else f"SI{code}")

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        self.send(f"MS{sound_mode}")
