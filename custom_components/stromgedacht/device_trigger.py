"""Device triggers for StromGedacht."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import state as state_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_ENTITY_ID, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo

from .const import DOMAIN

TRIGGER_TYPES = {"super_green", "green", "orange", "red"}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
        vol.Required(CONF_ENTITY_ID): str,
    }
)


async def async_get_triggers(hass: HomeAssistant, device_id: str) -> list[dict]:
    """Return device triggers for StromGedacht devices."""
    entity_reg = er.async_get(hass)
    triggers = []

    for entry in er.async_entries_for_device(entity_reg, device_id):
        if entry.domain == "sensor" and entry.unique_id and entry.unique_id.endswith("_state"):
            for trigger_type in TRIGGER_TYPES:
                triggers.append(
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_TYPE: trigger_type,
                        CONF_ENTITY_ID: entry.entity_id,
                    }
                )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: dict,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    state_config = {
        CONF_PLATFORM: "state",
        CONF_ENTITY_ID: [config[CONF_ENTITY_ID]],
        "to": config[CONF_TYPE],
    }
    state_config = await state_trigger.async_validate_trigger_config(hass, state_config)
    return await state_trigger.async_attach_trigger(
        hass, state_config, action, trigger_info, platform_type="device"
    )
