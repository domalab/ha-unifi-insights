"""Data update coordinator for UniFi Insights."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    UnifiInsightsAuthError,
    UnifiInsightsClient,
    UnifiInsightsConnectionError,
)
from .const import DOMAIN, SCAN_INTERVAL_NORMAL

_LOGGER = logging.getLogger(__name__)


class UnifiInsightsDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching UniFi Insights data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: UnifiInsightsClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL_NORMAL,
        )
        self.api = api
        self.config_entry = entry
        self._available = True
        self.data = {
            "sites": {},
            "devices": {},
            "clients": {},
            "stats": {},
            "last_update": None,
        }

    def get_site(self, site_id: str) -> dict[str, Any] | None:
        """Get site data by site ID."""
        return self.data.get("sites", {}).get(site_id)

    def get_device(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        """Get device data by site ID and device ID."""
        return self.data.get("devices", {}).get(site_id, {}).get(device_id)

    def get_device_stats(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        """Get device statistics by site ID and device ID."""
        return self.data.get("stats", {}).get(site_id, {}).get(device_id)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Get all sites first
            sites = await self.api.async_get_sites()
            self.data["sites"] = {site["id"]: site for site in sites}

            # For each site, get devices and clients
            for site_id in self.data["sites"]:
                try:
                    # Get devices first
                    devices = await self.api.async_get_devices(site_id)
                    self.data["devices"][site_id] = {}
                    self.data["stats"][site_id] = {}

                    # Get clients next
                    clients = await self.api.async_get_clients(site_id)
                    self.data["clients"][site_id] = {
                        client["id"]: client for client in clients
                    }

                    # Process each device
                    for device in devices:
                        device_id = device["id"]
                        device_name = device.get("name", device_id)

                        # Get device info to include firmware version
                        try:
                            device_info = await self.api.async_get_device_info(
                                site_id,
                                device_id
                            )
                            device.update(device_info)
                        except Exception as err:
                            _LOGGER.error(
                                "Error getting device info for %s (%s): %s",
                                device_name,
                                device_id,
                                err
                            )

                        # Store device data
                        self.data["devices"][site_id][device_id] = device

                        # Get and store device stats
                        try:
                            stats = await self.api.async_get_device_stats(
                                site_id,
                                device_id
                            )
                            # Add client data and device info to stats
                            stats["clients"] = [
                                c for c in clients 
                                if c.get("uplinkDeviceId") == device_id
                            ]
                            stats["id"] = device_id
                            self.data["stats"][site_id][device_id] = stats
                        except Exception as err:
                            _LOGGER.error(
                                "Error getting stats for device %s (%s): %s",
                                device_name,
                                device_id,
                                err
                            )
                            self.data["stats"][site_id][device_id] = {}

                    _LOGGER.debug(
                        "Successfully processed site %s with %d devices and %d clients",
                        site_id,
                        len(devices),
                        len(clients)
                    )

                except Exception as err:
                    _LOGGER.error(
                        "Error processing site %s: %s",
                        site_id,
                        err,
                        exc_info=True
                    )
                    continue

            self._available = True
            self.data["last_update"] = datetime.now()
            return self.data

        except UnifiInsightsAuthError as err:
            self._available = False
            raise ConfigEntryAuthFailed from err
        except UnifiInsightsConnectionError as err:
            self._available = False
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            self._available = False
            _LOGGER.error("Unexpected error updating data: %s", err, exc_info=True)
            raise UpdateFailed(f"Error updating data: {err}") from err

    @property
    def available(self) -> bool:
        """Return coordinator availability."""
        return self._available