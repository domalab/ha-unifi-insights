"""Support for UniFi Insights sensors."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .coordinator import UnifiInsightsDataUpdateCoordinator
from .entity import UnifiInsightsEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class UnifiInsightsSensorEntityDescription(SensorEntityDescription):
    """Class describing UniFi Insights sensor entities."""
    value_fn: callable[[dict[str, Any]], StateType] = None


SENSOR_TYPES: tuple[UnifiInsightsSensorEntityDescription, ...] = (
    UnifiInsightsSensorEntityDescription(
        key="cpu_usage",
        name="CPU Usage",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda stats: stats.get("cpuUtilizationPct"),
    ),
    UnifiInsightsSensorEntityDescription(
        key="memory_usage",
        name="Memory Usage",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda stats: stats.get("memoryUtilizationPct"),
    ),
    UnifiInsightsSensorEntityDescription(
        key="uptime",
        name="Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda stats: stats.get("uptimeSec"),
    ),
    UnifiInsightsSensorEntityDescription(
        key="tx_rate",
        name="TX Rate",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda stats: stats.get("uplink", {}).get("txRateBps"),
    ),
    UnifiInsightsSensorEntityDescription(
        key="rx_rate",
        name="RX Rate",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda stats: stats.get("uplink", {}).get("rxRateBps"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for UniFi Insights integration."""
    _LOGGER.debug("Setting up UniFi Insights sensors")
    
    coordinator: UnifiInsightsDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    
    # Add sensors for each device in each site
    for site_id, devices in coordinator.data["devices"].items():
        _LOGGER.debug(
            "Processing site %s with %d devices",
            site_id,
            len(devices)
        )
        for device_id in devices:
            _LOGGER.debug(
                "Creating sensors for device %s in site %s",
                device_id,
                site_id
            )
            entities.extend([
                UnifiInsightsSensor(
                    coordinator=coordinator,
                    description=description,
                    site_id=site_id,
                    device_id=device_id,
                )
                for description in SENSOR_TYPES
            ])
    
    _LOGGER.info(
        "Adding %d UniFi Insights sensors for %d devices",
        len(entities),
        len(coordinator.data["devices"])
    )
    async_add_entities(entities)


class UnifiInsightsSensor(UnifiInsightsEntity, SensorEntity):
    """Representation of a UniFi Insights Sensor."""

    entity_description: UnifiInsightsSensorEntityDescription

    def __init__(
        self,
        coordinator: UnifiInsightsDataUpdateCoordinator,
        description: UnifiInsightsSensorEntityDescription,
        site_id: str,
        device_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description, site_id, device_id)
        _LOGGER.debug(
            "Initializing %s sensor for device %s in site %s",
            description.key,
            device_id,
            site_id
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data["stats"].get(self._site_id, {}).get(self._device_id):
            _LOGGER.debug(
                "No stats available for sensor %s (device %s in site %s)",
                self.entity_description.key,
                self._device_id,
                self._site_id
            )
            return None
            
        stats = self.coordinator.data["stats"][self._site_id][self._device_id]
        value = self.entity_description.value_fn(stats)
        
        _LOGGER.debug(
            "Sensor %s for device %s in site %s updated to %s %s",
            self.entity_description.key,
            self._device_id,
            self._site_id,
            value,
            self.native_unit_of_measurement or ""
        )
        
        return value

    async def async_update(self) -> None:
        """Update the sensor."""
        await super().async_update()
        _LOGGER.debug(
            "Updated sensor %s for device %s in site %s",
            self.entity_description.key,
            self._device_id,
            self._site_id
        )