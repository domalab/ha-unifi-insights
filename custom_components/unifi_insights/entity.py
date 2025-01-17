"""UniFi Insights entity base class."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UnifiInsightsDataUpdateCoordinator


class UnifiInsightsEntity(CoordinatorEntity[UnifiInsightsDataUpdateCoordinator]):
    """Base class for UniFi Insights entities."""

    def __init__(
        self,
        coordinator: UnifiInsightsDataUpdateCoordinator,
        description: EntityDescription,
        site_id: str,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._site_id = site_id
        self._device_id = device_id
        self._attr_unique_id = f"{site_id}_{device_id}_{description.key}"

        # Get device info from coordinator's data
        device_data = coordinator.data["devices"][site_id][device_id]
        
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{site_id}_{device_id}")},
            manufacturer="Ubiquiti",
            model=device_data.get("model", "Unknown"),
            name=device_data.get("name", f"UniFi Device {device_id}"),
            sw_version=device_data.get("firmwareVersion", "Unknown"),
        )