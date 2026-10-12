"""DataUpdateCoordinator for StromGedacht."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    URL_STATES,
    URL_FORECAST,
    CONF_ZIP_CODE,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

type StromGedachtConfigEntry = ConfigEntry[StromGedachtDataUpdateCoordinator]


class StromGedachtDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching StromGedacht data."""

    config_entry: StromGedachtConfigEntry

    def __init__(self, hass: HomeAssistant, entry: StromGedachtConfigEntry) -> None:
        self.zip_code = entry.data[CONF_ZIP_CODE]

        # Interval from options or config
        scan_interval_min = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval_min),
        )

    async def _fetch(self, session: aiohttp.ClientSession, url: str, params: dict) -> Any:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                raise UpdateFailed(f"API error {response.status} from {url}")
            return await response.json()

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)

        params_states = {"zip": self.zip_code, "hoursInFuture": 24}
        params_forecast = {"zip": self.zip_code}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                data_states, data_forecast = await asyncio.gather(
                    self._fetch(session, URL_STATES, params_states),
                    self._fetch(session, URL_FORECAST, params_forecast),
                )
        except UpdateFailed:
            raise
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        return {
            "states": data_states.get("states", []),
            "forecast": data_forecast,
        }
