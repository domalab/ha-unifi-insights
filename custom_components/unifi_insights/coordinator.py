"""Data update coordinator for UniFi Insights."""
from __future__ import annotations

import asyncio
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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Get all sites first
            sites = await self.api.async_get_sites()
            self.data["sites"] = {site["id"]: site for site in sites}

            # For each site, get devices and clients
            for site_id in self.data["sites"]:
                devices = await self.api.async_get_devices(site_id)
                self.data["devices"][site_id] = {
                    device["id"]: device for device in devices
                }

                # Get stats for each device
                self.data["stats"][site_id] = {}
                for device in devices:
                    try:
                        stats = await self.api.async_get_device_stats(
                            site_id, device["id"]
                        )
                        self.data["stats"][site_id][device["id"]] = stats
                    except Exception as err:  # pylint: disable=broad-except
                        _LOGGER.error(
                            "Error getting stats for device %s: %s",
                            device["id"],
                            err,
                        )

                clients = await self.api.async_get_clients(site_id)
                self.data["clients"][site_id] = {
                    client["id"]: client for client in clients
                }

            self._available = True
            self.data["last_update"] = datetime.now()
            return self.data

        except UnifiInsightsAuthError as err:
            self._available = False
            raise ConfigEntryAuthFailed from err
        except UnifiInsightsConnectionError as err:
            self._available = False
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:  # pylint: disable=broad-except
            self._available = False
            raise UpdateFailed(f"Error updating data: {err}") from err

    @property
    def available(self) -> bool:
        """Return coordinator availability."""
        return self._available