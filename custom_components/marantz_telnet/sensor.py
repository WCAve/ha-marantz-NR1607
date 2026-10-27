"""Sensors for every value the receiver reports."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import AVRClient
from .descriptions import SensorDesc, describe
from .entity import AVREntity, setup_dynamic


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    client: AVRClient = entry.runtime_data
    setup_dynamic(
        entry, client, async_add_entities,
        lambda key: [AVRSensor(entry, client, d) for d in describe(key)],
    )


class AVRSensor(AVREntity, SensorEntity):
    """A single reported value."""

    def __init__(self, entry: ConfigEntry, client: AVRClient, desc: SensorDesc) -> None:
        super().__init__(entry, client, f"sensor_{desc.uid}", [desc.key], desc.listen_prefix)
        self._desc = desc
        self._attr_name = desc.name
        self._attr_icon = desc.icon
        self._attr_native_unit_of_measurement = desc.unit
        self._attr_entity_registry_enabled_default = desc.enabled
        if desc.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if desc.numeric:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Any:
        raw = self.raw()
        if raw is None:
            return None
        try:
            value = self._desc.value(raw, self._client.state)
        except (ValueError, TypeError, KeyError):
            return None
        if isinstance(value, str) and len(value) > 255:
            value = value[:255]
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attrs: dict[str, Any] = {"raw": self.raw()}
        if self._desc.attrs:
            attrs.update(self._desc.attrs(self._client.state))
        return attrs
