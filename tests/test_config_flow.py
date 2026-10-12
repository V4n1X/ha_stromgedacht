"""Tests for the StromGedacht config and options flow."""
from __future__ import annotations

import aiohttp
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.stromgedacht.const import (
    CONF_SCAN_INTERVAL,
    CONF_SHORT_STATUS,
    CONF_ZIP_CODE,
    DOMAIN,
    URL_FORECAST,
    URL_STATES,
)

from .conftest import FORECAST_RESPONSE, STATES_RESPONSE, ZIP_CODE


async def _start_flow(hass: HomeAssistant) -> str:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    return result["flow_id"]


async def test_user_flow_creates_entry(hass: HomeAssistant, mock_api: AiohttpClientMocker) -> None:
    flow_id = await _start_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_ZIP_CODE: f" {ZIP_CODE} ", CONF_SCAN_INTERVAL: 10, CONF_SHORT_STATUS: True}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"StromGedacht ({ZIP_CODE})"
    assert result["data"] == {
        CONF_ZIP_CODE: ZIP_CODE,
        CONF_SCAN_INTERVAL: 10,
        CONF_SHORT_STATUS: True,
    }
    assert result["result"].unique_id == ZIP_CODE
    await hass.async_block_till_done()
    assert result["result"].state is ConfigEntryState.LOADED


async def test_user_flow_invalid_zip_code(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    flow_id = await _start_flow(hass)

    result = await hass.config_entries.flow.async_configure(flow_id, {CONF_ZIP_CODE: "7017"})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_ZIP_CODE: "invalid_zip_code"}
    assert aioclient_mock.call_count == 0


async def test_user_flow_no_data_for_zip_code(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(URL_STATES, status=400, text="No data is available")
    flow_id = await _start_flow(hass)

    result = await hass.config_entries.flow.async_configure(flow_id, {CONF_ZIP_CODE: "12345"})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_ZIP_CODE: "no_data_for_zip_code"}


async def test_user_flow_cannot_connect_and_recover(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(URL_STATES, exc=aiohttp.ClientError)
    flow_id = await _start_flow(hass)

    result = await hass.config_entries.flow.async_configure(flow_id, {CONF_ZIP_CODE: ZIP_CODE})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL_STATES, json=STATES_RESPONSE)
    aioclient_mock.get(URL_FORECAST, json=FORECAST_RESPONSE)
    result = await hass.config_entries.flow.async_configure(flow_id, {CONF_ZIP_CODE: ZIP_CODE})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert result["result"].state is ConfigEntryState.LOADED


async def test_user_flow_server_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(URL_STATES, status=503)
    flow_id = await _start_flow(hass)

    result = await hass.config_entries.flow.async_configure(flow_id, {CONF_ZIP_CODE: ZIP_CODE})

    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_already_configured(
    hass: HomeAssistant, config_entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker
) -> None:
    config_entry.add_to_hass(hass)
    flow_id = await _start_flow(hass)

    result = await hass.config_entries.flow.async_configure(flow_id, {CONF_ZIP_CODE: ZIP_CODE})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert aioclient_mock.call_count == 0


async def test_options_flow_reloads_entry(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    entry = setup_integration
    assert hass.states.get("sensor.stromgedacht_70173_status").state == "super_green"

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 30, CONF_SHORT_STATUS: True}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_SCAN_INTERVAL: 30, CONF_SHORT_STATUS: True}
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.update_interval.total_seconds() == 30 * 60
