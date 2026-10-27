"""Config flow for the Marantz/Denon telnet integration."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .client import probe
from .const import DEFAULT_PORT, DOMAIN


class MarantzTelnetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the receiver address and check it answers."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()
            try:
                info = await probe(host, port)
            except (OSError, asyncio.TimeoutError, ConnectionError):
                errors["base"] = "cannot_connect"
            else:
                title = info.get("NSFRN") or info.get("SYMO") or host
                return self.async_create_entry(title=title, data={CONF_HOST: host, CONF_PORT: port})

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
