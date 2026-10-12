"""Tests for the StromGedacht device triggers."""
from __future__ import annotations

from datetime import timedelta

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_get_device_automations,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from custom_components.stromgedacht.const import DOMAIN, URL_FORECAST, URL_STATES

from .conftest import FORECAST_RESPONSE

STATUS = "sensor.stromgedacht_70173_status"


def _device_id(hass: HomeAssistant, entry: MockConfigEntry) -> str:
    [device] = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    return device.id


async def test_get_triggers(hass: HomeAssistant, setup_integration: MockConfigEntry) -> None:
    device_id = _device_id(hass, setup_integration)
    registry_id = er.async_get(hass).async_get(STATUS).id

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_id
    )

    # The sensor integration adds its own triggers for the power sensors
    assert [(t["type"], t["entity_id"]) for t in triggers if t["domain"] == DOMAIN] == [
        ("super_green", registry_id),
        ("green", registry_id),
        ("orange", registry_id),
        ("red", registry_id),
    ]


async def _change_api_state(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, freezer, state_code: int
) -> None:
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL_STATES, json={"states": [{"state": state_code}]})
    aioclient_mock.get(URL_FORECAST, json=FORECAST_RESPONSE)
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


async def _setup_automation(
    hass: HomeAssistant,
    device_id: str,
    entity_id: str,
    duration: dict | None = None,
) -> list:
    calls: list[ServiceCall] = []
    hass.services.async_register("test", "automation", calls.append)
    trigger = {
        "platform": "device",
        "domain": DOMAIN,
        "device_id": device_id,
        "entity_id": entity_id,
        "type": "red",
    }
    if duration is not None:
        trigger["for"] = duration
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": trigger,
                    "action": {"service": "test.automation", "data": {"trigger": "red"}},
                }
            ]
        },
    )
    await hass.async_block_till_done()
    return calls


async def test_trigger_fires_on_state_change(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    freezer,
) -> None:
    device_id = _device_id(hass, setup_integration)
    registry_id = er.async_get(hass).async_get(STATUS).id
    calls = await _setup_automation(hass, device_id, registry_id)

    await _change_api_state(hass, aioclient_mock, freezer, 3)
    assert hass.states.get(STATUS).state == "orange"
    assert len(calls) == 0

    await _change_api_state(hass, aioclient_mock, freezer, 4)
    assert hass.states.get(STATUS).state == "red"
    assert len(calls) == 1
    assert calls[0].data == {"trigger": "red"}


async def test_trigger_with_entity_id_from_pr3(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    freezer,
) -> None:
    """Automations saved with the plain entity_id keep working."""
    device_id = _device_id(hass, setup_integration)
    calls = await _setup_automation(hass, device_id, STATUS)

    await _change_api_state(hass, aioclient_mock, freezer, 4)
    assert len(calls) == 1


async def test_trigger_with_duration(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    freezer,
) -> None:
    """A trigger with 'for' fires only after the state held for that long."""
    device_id = _device_id(hass, setup_integration)
    registry_id = er.async_get(hass).async_get(STATUS).id
    calls = await _setup_automation(
        hass, device_id, registry_id, duration={"minutes": 10}
    )

    await _change_api_state(hass, aioclient_mock, freezer, 4)
    assert hass.states.get(STATUS).state == "red"
    assert len(calls) == 0

    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(calls) == 0

    freezer.tick(timedelta(minutes=6))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data == {"trigger": "red"}
