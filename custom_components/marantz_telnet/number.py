"""Number entities for levels, delays and timers."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import AVRClient
from .controls import NUMBERS, NumberDesc, channel_number
from .entity import AVREntity, setup_dynamic

_BY_KEY = {d.key: d for d in NUMBERS}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    client: AVRClient = entry.runtime_data

    def factory(key: str) -> list:
        desc = _BY_KEY.get(key) or channel_number(key)
        return [AVRNumber(entry, client, desc)] if desc else []

    setup_dynamic(entry, client, async_add_entities, factory)


class AVRNumber(AVREntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: ConfigEntry, client: AVRClient, desc: NumberDesc) -> None:
        super().__init__(entry, client, f"number_{desc.uid}", [desc.key])
        self._desc = desc
        self._attr_name = desc.name
        self._attr_icon = desc.icon
        self._attr_native_min_value = desc.minimum
        self._attr_native_max_value = desc.maximum
        self._attr_native_step = desc.step
        self._attr_native_unit_of_measurement = desc.unit

    @property
    def native_value(self) -> float | None:
        raw = self.raw()
        return None if raw is None else self._desc.decode(raw)

    async def async_set_native_value(self, value: float) -> None:
        self.send(self._desc.encode(value))
