"""Support for UniFi Insights binary sensors."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import UnifiInsightsDataUpdateCoordinator
from .entity import UnifiInsightsEntity

_LOGGER = logging.getLogger(__name__)

@dataclass
class UnifiInsightsBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing UniFi Insights binary sensor entities."""
    value_fn: callable[[dict[str, Any]], bool] = None

BINARY_SENSOR_TYPES: tuple[UnifiInsightsBinarySensorEntityDescription, ...] = (
    UnifiInsightsBinarySensorEntityDescription(
        key="device_status",
        name="Device Status",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda device: device.get("state") == "ONLINE",
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors for UniFi Insights integration."""
    coordinator: UnifiInsightsDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    _LOGGER.debug("Setting up binary sensors for UniFi Insights")
    
    # Add binary sensors for each device in each site
    for site_id, devices in coordinator.data["devices"].items():
        _LOGGER.debug("Processing site %s with %d devices", site_id, len(devices))
        for device_id in devices:
            entities.extend([
                UnifiInsightsBinarySensor(
                    coordinator=coordinator,
                    description=description,
                    site_id=site_id,
                    device_id=device_id,
                )
                for description in BINARY_SENSOR_TYPES
            ])
    
    _LOGGER.info("Adding %d UniFi Insights binary sensors", len(entities))
    async_add_entities(entities)


class UnifiInsightsBinarySensor(UnifiInsightsEntity, BinarySensorEntity):
    """Representation of a UniFi Insights Binary Sensor."""

    entity_description: UnifiInsightsBinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data["devices"].get(self._site_id, {}).get(self._device_id):
            _LOGGER.debug(
                "No device data for binary sensor %s_%s",
                self._site_id,
                self._device_id
            )
            return None
            
        device = self.coordinator.data["devices"][self._site_id][self._device_id]
        return self.entity_description.value_fn(device)