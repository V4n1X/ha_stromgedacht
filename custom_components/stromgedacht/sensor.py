"""Sensor platform for StromGedacht."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_SHORT_STATUS,
    CONF_ZIP_CODE,
    DEFAULT_SHORT_STATUS,
    STATE_SLUG_MAPPING,
)
from .coordinator import StromGedachtConfigEntry, StromGedachtDataUpdateCoordinator

DESCRIPTION_MAPPING = {
    -1: "Use electricity now to support grid stability",
    1: "Normal operation - no action required",
    3: "Reduce consumption to save costs and CO2",
    4: "Reduce consumption to prevent power shortages",
}

# Limit the forecast attribute to keep the state machine small
FORECAST_HISTORY = timedelta(hours=2)
FORECAST_MAX_ITEMS = 192
FORECAST_SLOT = timedelta(minutes=15)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StromGedachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor."""
    coordinator = entry.runtime_data

    async_add_entities([
        StromGedachtStateSensor(coordinator, entry),
        StromGedachtForecastSensor(coordinator, entry, "renewableEnergy", "renewable_energy"),
        StromGedachtForecastSensor(coordinator, entry, "load", "grid_load"),
        StromGedachtForecastSensor(coordinator, entry, "residualLoad", "residual_load"),
        StromGedachtForecastSensor(
            coordinator, entry, "superGreenThreshold", "super_green_threshold"
        ),
        StromGedachtNextPeriodSensor(
            coordinator, entry, "next_super_green", {"super_green"}
        ),
        StromGedachtNextPeriodSensor(
            coordinator, entry, "next_reduce_consumption", {"orange", "red"}
        ),
        StromGedachtBestTimeSensor(coordinator, entry),
    ])


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is not None and parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.UTC)
    return parsed


def _state_periods(states: list[dict[str, Any]]) -> list[tuple[datetime, datetime, str]]:
    """Return the periods as (start, end, state), consecutive equal states merged."""
    periods: list[tuple[datetime, datetime, str]] = []
    for item in states:
        start = _parse_datetime(item.get("from"))
        end = _parse_datetime(item.get("to"))
        state = STATE_SLUG_MAPPING.get(item.get("state"))
        if start is None or end is None or state is None:
            continue
        if periods and periods[-1][2] == state and periods[-1][1] >= start:
            periods[-1] = (periods[-1][0], end, state)
        else:
            periods.append((start, end, state))
    return periods


class StromGedachtEntity(CoordinatorEntity[StromGedachtDataUpdateCoordinator]):
    """Base entity, all sensors belong to one service device per zip code."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: StromGedachtDataUpdateCoordinator, entry: StromGedachtConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"StromGedacht {entry.data[CONF_ZIP_CODE]}",
            manufacturer="TransnetBW",
            model="StromGedacht API",
            configuration_url="https://stromgedacht.de",
            entry_type=DeviceEntryType.SERVICE,
        )


class StromGedachtStateSensor(StromGedachtEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(STATE_SLUG_MAPPING.values())
    # The forecast of upcoming states changes with every update and is not
    # useful in the history, so keep it out of the recorder database.
    _unrecorded_attributes = frozenset({"future_states"})

    def __init__(
        self, coordinator: StromGedachtDataUpdateCoordinator, entry: StromGedachtConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_state"
        short_status = entry.options.get(
            CONF_SHORT_STATUS,
            entry.data.get(CONF_SHORT_STATUS, DEFAULT_SHORT_STATUS)
        )
        self._attr_translation_key = "state_short" if short_status else "state"

    @property
    def _current_state_code(self) -> int | None:
        states = self.coordinator.data.get("states", [])
        if not states:
            return None
        return states[0].get("state")

    @property
    def native_value(self) -> str | None:
        return STATE_SLUG_MAPPING.get(self._current_state_code)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "description": DESCRIPTION_MAPPING.get(
                self._current_state_code, "Data not available"
            ),
            "future_states": self.coordinator.data.get("states", []),
            "zip_code": self._entry.data[CONF_ZIP_CODE],
        }


class StromGedachtForecastSensor(StromGedachtEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.MEGA_WATT
    # The forecast series is only meant for charts of the current state
    _unrecorded_attributes = frozenset({"data_series"})

    def __init__(
        self,
        coordinator: StromGedachtDataUpdateCoordinator,
        entry: StromGedachtConfigEntry,
        json_key: str,
        translation_key: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._json_key = json_key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{json_key}"

    @property
    def _forecast(self) -> list[dict[str, Any]]:
        return self.coordinator.data.get("forecast", {}).get(self._json_key, [])

    @property
    def native_value(self) -> float | None:
        now = dt_util.now()
        current_value = None

        for entry in self._forecast:
            entry_dt = _parse_datetime(entry.get("dateTime"))
            if entry_dt is None:
                continue
            if entry_dt > now:
                break
            try:
                current_value = float(entry["value"])
            except (KeyError, ValueError, TypeError):
                continue

        return current_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        start_limit = dt_util.now() - FORECAST_HISTORY
        limited_data = []

        for entry in self._forecast:
            if len(limited_data) >= FORECAST_MAX_ITEMS:
                break
            entry_dt = _parse_datetime(entry.get("dateTime"))
            if entry_dt is not None and entry_dt >= start_limit:
                limited_data.append(entry)

        return {"data_series": limited_data}


class StromGedachtNextPeriodSensor(StromGedachtEntity, SensorEntity):
    """Start of the current or next period with one of the given states."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: StromGedachtDataUpdateCoordinator,
        entry: StromGedachtConfigEntry,
        translation_key: str,
        states: set[str],
    ) -> None:
        super().__init__(coordinator, entry)
        self._states = states
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{translation_key}"

    @property
    def _period(self) -> tuple[datetime, datetime, str] | None:
        now = dt_util.now()
        for period in _state_periods(self.coordinator.data.get("states", [])):
            if period[2] in self._states and period[1] > now:
                return period
        return None

    @property
    def native_value(self) -> datetime | None:
        period = self._period
        return period[0] if period else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        period = self._period
        return {
            "end": period[1].isoformat() if period else None,
            "state": period[2] if period else None,
        }


class StromGedachtBestTimeSensor(StromGedachtEntity, SensorEntity):
    """Start of the forecast slot with the lowest residual load from now on.

    A low residual load means a high share of renewable energy, so this is
    the best time to run deferrable consumers.
    """

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "best_time"

    def __init__(
        self, coordinator: StromGedachtDataUpdateCoordinator, entry: StromGedachtConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_best_time"

    @property
    def _best_slot(self) -> tuple[datetime, float, datetime] | None:
        # Include the slot that is currently running
        start_limit = dt_util.now() - FORECAST_SLOT
        forecast = self.coordinator.data.get("forecast", {}).get("residualLoad", [])
        best: tuple[datetime, float] | None = None
        last: datetime | None = None

        for entry in forecast:
            entry_dt = _parse_datetime(entry.get("dateTime"))
            if entry_dt is None or entry_dt <= start_limit:
                continue
            try:
                value = float(entry["value"])
            except (KeyError, ValueError, TypeError):
                continue
            last = entry_dt
            if best is None or value < best[1]:
                best = (entry_dt, value)

        if best is None or last is None:
            return None
        return best[0], best[1], last + FORECAST_SLOT

    @property
    def native_value(self) -> datetime | None:
        slot = self._best_slot
        return slot[0] if slot else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        slot = self._best_slot
        return {
            "residual_load": slot[1] if slot else None,
            "forecast_until": slot[2].isoformat() if slot else None,
        }
