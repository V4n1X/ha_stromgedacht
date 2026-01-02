"""Config flow for StromGedacht integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN, 
    CONF_ZIP_CODE, 
    CONF_SCAN_INTERVAL, 
    DEFAULT_SCAN_INTERVAL, 
    MIN_SCAN_INTERVAL,
    URL_STATES
)

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    zip_code = data[CONF_ZIP_CODE]
    
    session = async_get_clientsession(hass)
    params = {"zip": zip_code, "hoursInFuture": 1}
    
    try:
        async with session.get(URL_STATES, params=params) as response:
            if response.status != 200:
                raise ValueError("Invalid API response")
            await response.json()
    except Exception as err:
        raise ValueError(f"Cannot connect: {err}") from err

    return {"title": f"StromGedacht ({zip_code})"}


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for StromGedacht (Nachträgliche Änderung)."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_options = self.entry.options
        current_data = self.entry.data
        
        current_interval = current_options.get(
            CONF_SCAN_INTERVAL, 
            current_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        schema = vol.Schema({
            vol.Optional(
                CONF_SCAN_INTERVAL, 
                default=current_interval
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
        })

        return self.async_show_form(step_id="init", data_schema=schema)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for StromGedacht."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_ZIP_CODE])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_ZIP_CODE): str,
            vol.Optional(
                CONF_SCAN_INTERVAL, 
                default=DEFAULT_SCAN_INTERVAL
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
        })

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )