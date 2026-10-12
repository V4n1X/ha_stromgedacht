"""Config flow for StromGedacht integration."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_ZIP_CODE,
    CONF_SCAN_INTERVAL,
    CONF_SHORT_STATUS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHORT_STATUS,
    MIN_SCAN_INTERVAL,
    REQUEST_TIMEOUT,
    URL_STATES,
)

_LOGGER = logging.getLogger(__name__)

ZIP_CODE_PATTERN = re.compile(r"^\d{5}$")


class CannotConnect(Exception):
    """Error to indicate the API is not reachable."""


class InvalidZipCode(Exception):
    """Error to indicate the API has no data for the zip code."""


async def validate_input(hass: HomeAssistant, zip_code: str) -> None:
    session = async_get_clientsession(hass)
    params = {"zip": zip_code, "hoursInFuture": 1}

    try:
        async with asyncio.timeout(REQUEST_TIMEOUT):
            async with session.get(URL_STATES, params=params) as response:
                # The API answers unknown or invalid zip codes with 400
                if response.status == 400:
                    raise InvalidZipCode
                if response.status != 200:
                    raise CannotConnect
                await response.json()
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        raise CannotConnect from err


def _settings_schema(scan_interval: int, short_status: bool) -> dict:
    return {
        vol.Optional(
            CONF_SCAN_INTERVAL,
            default=scan_interval
        ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
        vol.Optional(
            CONF_SHORT_STATUS,
            default=short_status
        ): bool,
    }


class OptionsFlowHandler(OptionsFlowWithReload):

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_options = self.config_entry.options
        current_data = self.config_entry.data

        current_interval = current_options.get(
            CONF_SCAN_INTERVAL,
            current_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        current_short_status = current_options.get(
            CONF_SHORT_STATUS,
            current_data.get(CONF_SHORT_STATUS, DEFAULT_SHORT_STATUS)
        )

        schema = vol.Schema(_settings_schema(current_interval, current_short_status))

        return self.async_show_form(step_id="init", data_schema=schema)


class StromGedachtConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            zip_code = str(user_input[CONF_ZIP_CODE]).strip()

            if not ZIP_CODE_PATTERN.match(zip_code):
                errors[CONF_ZIP_CODE] = "invalid_zip_code"
            else:
                await self.async_set_unique_id(zip_code)
                self._abort_if_unique_id_configured()

                try:
                    await validate_input(self.hass, zip_code)
                except InvalidZipCode:
                    errors[CONF_ZIP_CODE] = "no_data_for_zip_code"
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(
                        title=f"StromGedacht ({zip_code})",
                        data={**user_input, CONF_ZIP_CODE: zip_code},
                    )

        schema = vol.Schema({
            vol.Required(CONF_ZIP_CODE): str,
            **_settings_schema(DEFAULT_SCAN_INTERVAL, DEFAULT_SHORT_STATUS),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )
