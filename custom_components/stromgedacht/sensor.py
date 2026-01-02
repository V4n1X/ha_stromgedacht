"""Sensor platform for StromGedacht."""
from __future__ import annotations

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

from .const import DOMAIN
from .coordinator import StromGedachtDataUpdateCoordinator

# Status Mappings
STATE_MAPPING = {
    -1: "Supergrün (Netzdienlich)",
    1: "Grün (Normalbetrieb)",
    3: "Orange (Verbrauch reduzieren)",
    4: "Rot (Strommangel vermeiden)",
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
    
    # 1. Ampel Sensor
    entities.append(StromGedachtStateSensor(coordinator, entry))
    
    # 2. Forecast Sensoren
    if coordinator.data and "forecast" in coordinator.data:
        entities.append(StromGedachtForecastSensor(
            coordinator, entry, "renewableEnergy", "Erneuerbare Energie", "mdi:solar-power"
        ))
        entities.append(StromGedachtForecastSensor(
            coordinator, entry, "load", "Netzlast", "mdi:transmission-tower"
        ))
        entities.append(StromGedachtForecastSensor(
            coordinator, entry, "residualLoad", "Residuallast", "mdi:chart-line"
        ))

    async_add_entities(entities)


class StromGedachtStateSensor(CoordinatorEntity, SensorEntity):
    """Sensor (Ampel)."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Status"
        self._attr_unique_id = f"{entry.entry_id}_state"
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Information about the device (Service)."""
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
            return "Unbekannt"
        
        current_state_code = states[0].get("state", 0)
        return STATE_MAPPING.get(current_state_code, f"Unbekannt ({current_state_code})")

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
        
        description = "Daten nicht verfügbar"
        if current_code == -1:
            description = "Strom jetzt nutzen, um die Netzdienlichkeit zu unterstützen"
        elif current_code == 1:
            description = "Normalbetrieb – Du musst nichts weiter tun"
        elif current_code == 3:
            description = "Verbrauch reduzieren, um Kosten und CO2 zu sparen"
        elif current_code == 4:
            description = "Verbrauch reduzieren, um Strommangel zu verhindern"

        return {
            "description": description,
            "future_states": states,
            "zip_code": self._entry.data['zip_code']
        }


class StromGedachtForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor für numerische Werte (MW)."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.MEGA_WATT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, json_key, name_suffix, icon):
        super().__init__(coordinator)
        self._entry = entry
        self._json_key = json_key
        # Der Name wird durch has_entity_name automatisch mit dem Gerätenamen kombiniert
        self._attr_name = name_suffix
        self._attr_unique_id = f"{entry.entry_id}_{json_key}"
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        """Link to the same device as the state sensor."""
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
        try:
            return float(forecast_data[0].get("value", 0))
        except (IndexError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "data_series": self.coordinator.data.get("forecast", {}).get(self._json_key, [])
        }