"""Marantz/Denon AVR over telnet: exposes everything the receiver reports."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .client import AVRClient
from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.MEDIA_PLAYER,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.NUMBER,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_SEND_COMMAND = "send_command"
SEND_SCHEMA = vol.Schema(
    {
        vol.Required("command"): vol.Any(cv.string, [cv.string]),
        vol.Optional("config_entry_id"): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the raw command service."""

    async def _send(call: ServiceCall) -> None:
        commands = call.data["command"]
        if isinstance(commands, str):
            commands = [commands]
        target = call.data.get("config_entry_id")
        entries = [
            e
            for e in hass.config_entries.async_entries(DOMAIN)
            if e.state is ConfigEntryState.LOADED and (target is None or e.entry_id == target)
        ]
        if not entries:
            raise HomeAssistantError("No loaded Marantz telnet receiver found")
        for entry in entries:
            client: AVRClient = entry.runtime_data
            try:
                for cmd in commands:
                    client.send(cmd)
            except ConnectionError as err:
                raise HomeAssistantError(str(err)) from err

    hass.services.async_register(DOMAIN, SERVICE_SEND_COMMAND, _send, schema=SEND_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Connect to the receiver and set up entities."""
    client = AVRClient(entry.data[CONF_HOST], entry.data.get(CONF_PORT, DEFAULT_PORT))
    client.start(
        lambda coro: entry.async_create_background_task(hass, coro, f"{DOMAIN}_{entry.entry_id}")
    )
    if not await client.wait_for(["PW"], 15):
        await client.stop()
        raise ConfigEntryNotReady(
            f"No response from {entry.data[CONF_HOST]}. The receiver allows only one telnet "
            "connection, so close any other app using it."
        )
    # Identity + the first full poll; entities for later keys are added as they arrive.
    await client.wait_for(["SYMO", "NSFRN", "SSINFFRM:AVR", "SSSOD:TV"], 8)
    await client.wait_for(["SSSOD:AUX1", "Z2PW", "SSLEV:FL"], 12)

    name = client.state.get("NSFRN") or entry.title
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Denon" if name.lower().startswith("denon") else "Marantz",
        model=client.state.get("SYMO"),
        name=name,
        sw_version=client.state.get("SSINFFRM:AVR"),
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )

    entry.runtime_data = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Disconnect."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        await entry.runtime_data.stop()
    return ok
