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

from .conftest import FORECAST_RESPONSE, NO_FORECAST, NOW, STATES_RESPONSE

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
        f"{entry_id}_superGreenThreshold",
        f"{entry_id}_next_super_green",
        f"{entry_id}_next_reduce_consumption",
        f"{entry_id}_best_time",
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
        "sensor.stromgedacht_70173_super_green_threshold": "1850.0",
    }
    for entity_id, value in expected.items():
        state = hass.states.get(entity_id)
        assert state.state == value, entity_id
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "MW"
        assert len(state.attributes["data_series"]) == 4


async def test_planning_sensors(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    # The super green period is running since 12:00
    state = hass.states.get("sensor.stromgedacht_70173_next_super_green")
    assert state.state == "2026-10-12T12:00:00+00:00"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TIMESTAMP
    assert state.attributes["end"] == "2026-10-12T16:00:00+00:00"
    assert state.attributes["state"] == "super_green"

    # Both orange periods are merged, red follows afterwards
    state = hass.states.get("sensor.stromgedacht_70173_next_reduce_consumption")
    assert state.state == "2026-10-12T16:00:00+00:00"
    assert state.attributes["end"] == "2026-10-12T21:00:00+00:00"
    assert state.attributes["state"] == "orange"

    # The 11:45 slot is over, 12:15 has the lowest residual load
    state = hass.states.get("sensor.stromgedacht_70173_best_consumption_time")
    assert state.state == "2026-10-12T12:15:00+00:00"
    assert state.attributes["residual_load"] == 4300
    assert state.attributes["forecast_until"] == "2026-10-12T12:45:00+00:00"


async def test_planning_sensors_follow_time(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    freezer,
) -> None:
    # At 16:30 the super green period is over and the forecast has ended
    freezer.move_to("2026-10-12T16:30:00+00:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get("sensor.stromgedacht_70173_next_super_green").state == "unknown"
    assert hass.states.get("sensor.stromgedacht_70173_best_consumption_time").state == "unknown"
    state = hass.states.get("sensor.stromgedacht_70173_next_reduce_consumption")
    assert state.state == "2026-10-12T16:00:00+00:00"


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


FORECAST_ENTITIES = (
    "sensor.stromgedacht_70173_grid_load",
    "sensor.stromgedacht_70173_renewable_energy",
    "sensor.stromgedacht_70173_residual_load",
    "sensor.stromgedacht_70173_super_green_threshold",
    "sensor.stromgedacht_70173_best_consumption_time",
)


async def _setup_limited(
    hass: HomeAssistant, config_entry: MockConfigEntry, freezer
) -> None:
    freezer.move_to(NOW)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_limited_zip_code_without_forecast_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api_limited: AiohttpClientMocker,
    freezer,
) -> None:
    """Without forecast only the sensors based on the grid states are created."""
    await _setup_limited(hass, config_entry, freezer)

    assert config_entry.state is ConfigEntryState.LOADED
    entity_registry = er.async_get(hass)
    unique_ids = {
        entity.unique_id
        for entity in er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    }
    entry_id = config_entry.entry_id
    assert unique_ids == {
        f"{entry_id}_state",
        f"{entry_id}_next_super_green",
        f"{entry_id}_next_reduce_consumption",
    }
    assert hass.states.get(STATUS).state == "super_green"
    assert (
        hass.states.get("sensor.stromgedacht_70173_next_super_green").state
        == "2026-10-12T12:00:00+00:00"
    )


async def test_forecast_entities_added_when_forecast_appears(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api_limited: AiohttpClientMocker,
    freezer,
) -> None:
    await _setup_limited(hass, config_entry, freezer)
    for entity_id in FORECAST_ENTITIES:
        assert hass.states.get(entity_id) is None

    mock_api_limited.clear_requests()
    mock_api_limited.get(URL_STATES, json=STATES_RESPONSE)
    mock_api_limited.get(URL_FORECAST, json=FORECAST_RESPONSE)
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # 12:23 now, so the 12:15 value is the current one
    assert hass.states.get("sensor.stromgedacht_70173_residual_load").state == "4300.0"
    for entity_id in FORECAST_ENTITIES:
        assert hass.states.get(entity_id).state != STATE_UNAVAILABLE, entity_id

    # Further updates must not add the entities again
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(er.async_entries_for_config_entry(er.async_get(hass), config_entry.entry_id)) == 8


async def test_forecast_entities_unavailable_when_forecast_disappears(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    freezer,
) -> None:
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL_STATES, json=STATES_RESPONSE)
    aioclient_mock.get(URL_FORECAST, status=404, text=NO_FORECAST)
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(STATUS).state == "super_green"
    for entity_id in FORECAST_ENTITIES:
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE, entity_id


async def test_forecast_server_error_fails_update(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    freezer,
) -> None:
    """Only a 404 means no forecast, other errors are API outages."""
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL_STATES, json=STATES_RESPONSE)
    aioclient_mock.get(URL_FORECAST, status=500)
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(STATUS).state == STATE_UNAVAILABLE


def test_large_attributes_not_recorded() -> None:
    assert "future_states" in StromGedachtStateSensor._unrecorded_attributes
    assert "data_series" in StromGedachtForecastSensor._unrecorded_attributes
