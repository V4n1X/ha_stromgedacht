"""Fixtures for StromGedacht tests."""
from __future__ import annotations

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from homeassistant.core import HomeAssistant

from custom_components.stromgedacht.const import (
    CONF_SCAN_INTERVAL,
    CONF_SHORT_STATUS,
    CONF_ZIP_CODE,
    DOMAIN,
    URL_FORECAST,
    URL_STATES,
)

ZIP_CODE = "70173"
NOW = "2026-10-12T12:07:00+00:00"

STATES_RESPONSE = {
    "states": [
        {"from": "2026-10-12T12:00:00+00:00", "to": "2026-10-12T16:00:00+00:00", "state": -1},
        {"from": "2026-10-12T16:00:00+00:00", "to": "2026-10-12T20:00:00+00:00", "state": 3},
        {"from": "2026-10-12T20:00:00+00:00", "to": "2026-10-12T21:00:00+00:00", "state": 3},
        {"from": "2026-10-12T21:00:00+00:00", "to": "2026-10-12T22:00:00+00:00", "state": 4},
    ]
}


def _series(*values: float) -> list[dict[str, Any]]:
    """Return a 15 minute series starting at 11:45 UTC."""
    times = ["11:45", "12:00", "12:15", "12:30"]
    return [
        {"dateTime": f"2026-10-12T{time}:00Z", "value": value}
        for time, value in zip(times, values, strict=True)
    ]


FORECAST_RESPONSE = {
    "load": _series(5000, 5100, 5200, 5300),
    "renewableEnergy": _series(600, 650.5, 700, 750),
    "residualLoad": _series(4400, 4449.5, 4300, 4550),
    "superGreenThreshold": _series(1800, 1850, 1900, 1950),
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading the custom integration in all tests."""


@pytest.fixture
def mock_api(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Mock a healthy StromGedacht API."""
    aioclient_mock.get(URL_STATES, json=STATES_RESPONSE)
    aioclient_mock.get(URL_FORECAST, json=FORECAST_RESPONSE)
    return aioclient_mock


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a config entry as created by the config flow."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"StromGedacht ({ZIP_CODE})",
        unique_id=ZIP_CODE,
        data={CONF_ZIP_CODE: ZIP_CODE, CONF_SCAN_INTERVAL: 15, CONF_SHORT_STATUS: False},
    )


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: AiohttpClientMocker, freezer
) -> MockConfigEntry:
    """Set up the integration with the mocked API."""
    freezer.move_to(NOW)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
