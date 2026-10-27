"""Switch entities for on/off settings."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import AVRClient
from .controls import SWITCHES, SwitchDesc
from .entity import AVREntity, setup_dynamic

_BY_KEY = {d.key: d for d in SWITCHES}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    client: AVRClient = entry.runtime_data
    setup_dynamic(
        entry, client, async_add_entities,
        lambda key: [AVRSwitch(entry, client, _BY_KEY[key])] if key in _BY_KEY else [],
    )


class AVRSwitch(AVREntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry, client: AVRClient, desc: SwitchDesc) -> None:
        super().__init__(entry, client, f"switch_{desc.uid}", [desc.key])
        self._desc = desc
        self._attr_name = desc.name
        self._attr_icon = desc.icon

    @property
    def is_on(self) -> bool | None:
        raw = self.raw()
        return None if raw is None else raw == "ON"

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.send(self._desc.command.format(v="ON"))

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.send(self._desc.command.format(v="OFF"))
