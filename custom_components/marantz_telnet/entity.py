"""Shared entity helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import AVRClient
from .const import DOMAIN


class AVREntity(Entity):
    """Base entity bound to one or more protocol keys."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        client: AVRClient,
        uid: str,
        keys: Iterable[str],
        listen_prefix: str | None = None,
    ) -> None:
        self._client = client
        self._keys = tuple(keys)
        self._listen_prefix = listen_prefix
        self._attr_unique_id = f"{entry.entry_id}_{uid}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    async def async_added_to_hass(self) -> None:
        for key in self._keys:
            self.async_on_remove(self._client.add_listener(key, self._on_update))
        if self._listen_prefix:
            self.async_on_remove(self._client.add_listener("*", self._on_prefix))
        self.async_on_remove(self._client.add_connection_listener(self._on_update))

    @callback
    def _on_update(self, _key: str = "") -> None:
        if self.hass is not None:
            self.async_write_ha_state()

    @callback
    def _on_prefix(self, key: str) -> None:
        if key.startswith(self._listen_prefix) and key not in self._keys:  # type: ignore[arg-type]
            self._on_update(key)

    @property
    def available(self) -> bool:
        return self._client.connected and (not self._keys or self._keys[0] in self._client.state)

    def raw(self, key: str | None = None) -> str | None:
        return self._client.state.get(key or self._keys[0])

    def send(self, *commands: str) -> None:
        try:
            for cmd in commands:
                self._client.send(cmd)
        except ConnectionError as err:
            raise HomeAssistantError(str(err)) from err


def setup_dynamic(
    entry: ConfigEntry,
    client: AVRClient,
    async_add_entities: AddEntitiesCallback,
    factory: Callable[[str], list[Entity]],
) -> None:
    """Create entities for known keys now and for new keys as they appear."""
    created: set[str] = set()

    @callback
    def _add(key: str) -> None:
        new = [e for e in factory(key) if e.unique_id not in created]
        for ent in new:
            created.add(ent.unique_id)  # type: ignore[arg-type]
        if new:
            async_add_entities(new)

    for key in list(client.state):
        _add(key)
    entry.async_on_unload(client.add_new_key_listener(_add))
