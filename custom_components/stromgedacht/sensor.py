"""Sensor platform for StromGedacht."""
from __future__ import annotations

from datetime import timedelta
from dateutil.parser import parse
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_SHORT_STATUS, DEFAULT_SHORT_STATUS
from .coordinator import StromGedachtDataUpdateCoordinator

STATE_SLUG_MAPPING = {
    -1: "super_green",
    1: "green",
    3: "orange",
    4: "red",
}

ICON_MAPPING = {
    -1: "mdi:leaf",
    1: "mdi:check-circle",
    3: "mdi:alert",
    4: "mdi:lightning-bolt",
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor."""
    coordinator: StromGedachtDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    entities.append(StromGedachtStateSensor(coordinator, entry))
    if coordinator.data and "forecast" in coordinator.data:
        entities.append(StromGedachtForecastSensor(
            coordinator, entry, "renewableEnergy", "renewable_energy", "mdi:solar-power"
        ))
        entities.append(StromGedachtForecastSensor(
            coordinator, entry, "load", "grid_load", "mdi:transmission-tower"
        ))
        entities.append(StromGedachtForecastSensor(
            coordinator, entry, "residualLoad", "residual_load", "mdi:chart-line"
        ))

    async_add_entities(entities)


class StromGedachtStateSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_state"
        self._attr_has_entity_name = True

    @property
    def translation_key(self) -> str:
        short_status = self._entry.options.get(
            CONF_SHORT_STATUS, 
            self._entry.data.get(CONF_SHORT_STATUS, DEFAULT_SHORT_STATUS)
        )
        return "state_short" if short_status else "state"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"StromGedacht {self._entry.data['zip_code']}",
            manufacturer="TransnetBW",
            model="StromGedacht API",
            configuration_url="https://stromgedacht.de",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str | None:
        states = self.coordinator.data.get("states", [])
        if not states:
            return "unknown"
        
        current_state_code = states[0].get("state", 0)
        return STATE_SLUG_MAPPING.get(current_state_code, "unknown")

    @property
    def icon(self) -> str:
        states = self.coordinator.data.get("states", [])
        if not states:
            return "mdi:help-circle"
        
        current_state_code = states[0].get("state", 1)
        return ICON_MAPPING.get(current_state_code, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict:
        states = self.coordinator.data.get("states", [])
        current_code = states[0].get("state", 0) if states else 0
        
        description = "Data not available"
        if current_code == -1:
            description = "Use electricity now to support grid stability"
        elif current_code == 1:
            description = "Normal operation – no action required"
        elif current_code == 3:
            description = "Reduce consumption to save costs and CO2"
        elif current_code == 4:
            description = "Reduce consumption to prevent power shortages"

        return {
            "description": description,
            "future_states": states,
            "zip_code": self._entry.data['zip_code']
        }


class StromGedachtForecastSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.MEGA_WATT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, json_key, translation_key, icon):
        super().__init__(coordinator)
        self._entry = entry
        self._json_key = json_key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{json_key}"
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"StromGedacht {self._entry.data['zip_code']}",
            manufacturer="TransnetBW",
            model="StromGedacht API",
            configuration_url="https://stromgedacht.de",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> float | None:
        forecast_data = self.coordinator.data.get("forecast", {}).get(self._json_key, [])
        
        if not forecast_data:
            return None

        now = dt_util.now()
        current_value = None

        for entry in forecast_data:
            try:
                entry_dt = parse(entry["dateTime"])
                if entry_dt.tzinfo is None:
                    entry_dt = entry_dt.replace(tzinfo=dt_util.UTC)

                if entry_dt <= now:
                    current_value = float(entry["value"])
                else:
                    break
            except (ValueError, TypeError):
                continue
        
        return current_value

    @property
    def extra_state_attributes(self) -> dict:
        raw_data = self.coordinator.data.get("forecast", {}).get(self._json_key, [])
        
        if not raw_data:
            return {}

        now = dt_util.now()
        limited_data = []

        start_limit = now - timedelta(hours=2)
        
        count = 0
        MAX_ITEMS = 192

        for entry in raw_data:
            if count >= MAX_ITEMS:
                break
            
            try:
                entry_dt = parse(entry["dateTime"])
                if entry_dt.tzinfo is None:
                    entry_dt = entry_dt.replace(tzinfo=dt_util.UTC)

                if entry_dt >= start_limit:
                    limited_data.append(entry)
                    count += 1
            except (ValueError, TypeError):
                continue

        return {
            "data_series": limited_data
        }