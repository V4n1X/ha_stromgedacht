"""DataUpdateCoordinator for StromGedacht."""
from datetime import timedelta
import logging
import asyncio
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN, 
    URL_STATES, 
    URL_FORECAST, 
    CONF_ZIP_CODE, 
    CONF_SCAN_INTERVAL, 
    DEFAULT_SCAN_INTERVAL
)

_LOGGER = logging.getLogger(__name__)

class StromGedachtDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching StromGedacht data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.zip_code = entry.data[CONF_ZIP_CODE]
        
        # Interval from options or config
        scan_interval_min = entry.options.get(
            CONF_SCAN_INTERVAL, 
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval_min),
        )

    async def _async_update_data(self):
        session = async_get_clientsession(self.hass)
        
        params_states = {"zip": self.zip_code, "hoursInFuture": 24}
        params_forecast = {"zip": self.zip_code} 

        try:
            async with async_timeout.timeout(20):
                # Parallel fetch
                task1 = session.get(URL_STATES, params=params_states)
                task2 = session.get(URL_FORECAST, params=params_forecast)

                resp_states, resp_forecast = await asyncio.gather(task1, task2)

                if resp_states.status != 200:
                    raise UpdateFailed(f"States API Error: {resp_states.status}")
                if resp_forecast.status != 200:
                    raise UpdateFailed(f"Forecast API Error: {resp_forecast.status}")

                data_states = await resp_states.json()
                data_forecast = await resp_forecast.json()

                # Merge data
                return {
                    "states": data_states.get("states", []),
                    "forecast": data_forecast
                }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")