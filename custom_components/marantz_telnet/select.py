"""Select entities for multi-value settings."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import AVRClient
from .controls import DEFAULT_CONTROLS, SELECTS, SelectDesc
from .entity import AVREntity, setup_dynamic

_BY_KEY: dict[str, list[SelectDesc]] = {}
for _d in SELECTS:
    _BY_KEY.setdefault(_d.key, []).append(_d)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    client: AVRClient = entry.runtime_data
    setup_dynamic(
        entry, client, async_add_entities,
        lambda key: [AVRSelect(entry, client, d) for d in _BY_KEY.get(key, [])],
    )


class AVRSelect(AVREntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry, client: AVRClient, desc: SelectDesc) -> None:
        super().__init__(entry, client, f"select_{desc.uid}", [desc.key])
        self._desc = desc
        self._attr_name = desc.name
        self._attr_icon = desc.icon
        self._attr_entity_registry_enabled_default = desc.uid in DEFAULT_CONTROLS
        self._attr_options = list(desc.options.values())

    @property
    def current_option(self) -> str | None:
        raw = self.raw()
        return None if raw is None else self._desc.options.get(raw)

    async def async_select_option(self, option: str) -> None:
        for value, label in self._desc.options.items():
            if label == option:
                self.send(self._desc.command.format(v=value))
                return
