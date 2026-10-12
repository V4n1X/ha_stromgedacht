"""Tests for the StromGedacht setup and sensors."""
from __future__ import annotations

from datetime import timedelta

from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from homeassistant.components.sensor import ATTR_OPTIONS, SensorDeviceClass
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_UNIT_OF_MEASUREMENT, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.stromgedacht.const import DOMAIN, URL_FORECAST, URL_STATES
from custom_components.stromgedacht.sensor import (
    StromGedachtForecastSensor,
    StromGedachtStateSensor,
)

from .conftest import FORECAST_RESPONSE, STATES_RESPONSE

STATUS = "sensor.stromgedacht_70173_status"


async def test_setup_and_unload(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    entry = setup_integration
    assert entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retry_when_api_unavailable(
    hass: HomeAssistant, config_entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(URL_STATES, status=500)
    aioclient_mock.get(URL_FORECAST, json=FORECAST_RESPONSE)
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_entities_keep_unique_ids(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    """Unique IDs must not change, otherwise users lose their entities."""
    entry_id = setup_integration.entry_id
    entity_registry = er.async_get(hass)
    unique_ids = {
        entity.unique_id
        for entity in er.async_entries_for_config_entry(entity_registry, entry_id)
    }
    assert unique_ids == {
        f"{entry_id}_state",
        f"{entry_id}_renewableEnergy",
        f"{entry_id}_load",
        f"{entry_id}_residualLoad",
    }

    [device] = dr.async_entries_for_config_entry(dr.async_get(hass), entry_id)
    assert device.identifiers == {(DOMAIN, entry_id)}
    assert device.name == "StromGedacht 70173"
    assert device.entry_type is dr.DeviceEntryType.SERVICE


async def test_status_sensor(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    state = hass.states.get(STATUS)
    assert state.state == "super_green"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENUM
    assert state.attributes[ATTR_OPTIONS] == ["super_green", "green", "orange", "red"]
    assert state.attributes["description"] == "Use electricity now to support grid stability"
    assert state.attributes["future_states"] == STATES_RESPONSE["states"]
    assert state.attributes["zip_code"] == "70173"
    assert state.attributes["friendly_name"] == "StromGedacht 70173 Status"


async def test_forecast_sensors(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    # NOW is 12:07, so the 12:00 value is the current one
    expected = {
        "sensor.stromgedacht_70173_grid_load": "5100.0",
        "sensor.stromgedacht_70173_renewable_energy": "650.5",
        "sensor.stromgedacht_70173_residual_load": "4449.5",
    }
    for entity_id, value in expected.items():
        state = hass.states.get(entity_id)
        assert state.state == value, entity_id
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "MW"
        assert len(state.attributes["data_series"]) == 4


async def test_unknown_state_and_api_outage(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    freezer,
) -> None:
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL_STATES, json={"states": []})
    aioclient_mock.get(URL_FORECAST, json=FORECAST_RESPONSE)
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(STATUS)
    assert state.state == "unknown"
    assert state.attributes["description"] == "Data not available"

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL_STATES, status=500)
    aioclient_mock.get(URL_FORECAST, json=FORECAST_RESPONSE)
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(STATUS).state == STATE_UNAVAILABLE


def test_large_attributes_not_recorded() -> None:
    assert "future_states" in StromGedachtStateSensor._unrecorded_attributes
    assert "data_series" in StromGedachtForecastSensor._unrecorded_attributes
