"""UniFi Insights API Client."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_API_HOST, UNIFI_API_HEADERS

_LOGGER = logging.getLogger(__name__)


class UnifiInsightsError(Exception):
    """Base class for UniFi Insights errors."""


class UnifiInsightsAuthError(UnifiInsightsError):
    """Authentication error."""


class UnifiInsightsConnectionError(UnifiInsightsError):
    """Connection error."""


class UnifiInsightsClient:
    """UniFi Insights API client."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        host: str = DEFAULT_API_HOST,
        session: ClientSession | None = None,
    ) -> None:
        """Initialize the API client."""
        _LOGGER.debug("Initializing UniFi Insights API client with host: %s", host)
        self._hass = hass
        self._api_key = api_key
        self._host = host
        self._session = session or async_get_clientsession(hass)
        self._request_lock = asyncio.Lock()
        _LOGGER.info("UniFi Insights API client initialized")

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an API request."""
        async with self._request_lock:
            headers = {
                **UNIFI_API_HEADERS,
                "X-API-Key": self._api_key,
            }

            if "headers" in kwargs:
                _LOGGER.debug("Additional headers provided for request")
                headers.update(kwargs.pop("headers"))

            url = f"{self._host}/proxy/network/integration{endpoint}"
            _LOGGER.debug("Making %s request to %s", method, url)

            try:
                async with self._session.request(
                    method, url, headers=headers, **kwargs
                ) as resp:
                    _LOGGER.debug(
                        "Response received from %s - Status: %s",
                        endpoint,
                        resp.status
                    )

                    if resp.status == 401:
                        _LOGGER.error("Authentication failed - invalid API key")
                        raise UnifiInsightsAuthError("Invalid API key")
                    
                    if resp.status == 403:
                        _LOGGER.error("Authorization failed - API key lacks permission")
                        raise UnifiInsightsAuthError("API key lacks permission")

                    resp.raise_for_status()
                    response_data = await resp.json()
                    _LOGGER.debug(
                        "Successfully processed response from %s", 
                        endpoint
                    )
                    return response_data

            except asyncio.TimeoutError as err:
                _LOGGER.error("Request timed out for %s: %s", url, err)
                raise UnifiInsightsConnectionError(
                    f"Timeout connecting to {url}"
                ) from err
            except ClientError as err:
                _LOGGER.error("Connection error for %s: %s", url, err)
                raise UnifiInsightsConnectionError(
                    f"Error connecting to {url}: {err}"
                ) from err

    async def async_get_sites(self) -> list[dict[str, Any]]:
        """Get all sites."""
        _LOGGER.debug("Fetching all sites")
        try:
            response = await self._request("GET", "/v1/sites")
            sites = response.get("data", [])
            _LOGGER.info("Successfully retrieved %d sites", len(sites))
            return sites
        except Exception as err:
            _LOGGER.error("Failed to fetch sites: %s", err)
            raise

    async def async_get_devices(self, site_id: str) -> list[dict[str, Any]]:
        """Get all devices for a site."""
        _LOGGER.debug("Fetching devices for site %s", site_id)
        try:
            response = await self._request("GET", f"/v1/sites/{site_id}/devices")
            devices = response.get("data", [])
            _LOGGER.info(
                "Successfully retrieved %d devices for site %s",
                len(devices),
                site_id
            )
            return devices
        except Exception as err:
            _LOGGER.error("Failed to fetch devices for site %s: %s", site_id, err)
            raise

    async def async_get_device_stats(
        self, site_id: str, device_id: str
    ) -> dict[str, Any]:
        """Get device statistics."""
        _LOGGER.debug(
            "Fetching statistics for device %s in site %s",
            device_id,
            site_id
        )
        try:
            response = await self._request(
                "GET",
                f"/v1/sites/{site_id}/devices/{device_id}/statistics/latest"
            )
            _LOGGER.info(
                "Successfully retrieved stats for device %s in site %s",
                device_id,
                site_id
            )
            return response
        except Exception as err:
            _LOGGER.error(
                "Failed to fetch stats for device %s in site %s: %s",
                device_id,
                site_id,
                err
            )
            raise

    async def async_get_clients(self, site_id: str) -> list[dict[str, Any]]:
        """Get all clients for a site."""
        _LOGGER.debug("Fetching clients for site %s", site_id)
        try:
            response = await self._request("GET", f"/v1/sites/{site_id}/clients")
            clients = response.get("data", [])
            _LOGGER.info(
                "Successfully retrieved %d clients for site %s",
                len(clients),
                site_id
            )
            return clients
        except Exception as err:
            _LOGGER.error("Failed to fetch clients for site %s: %s", site_id, err)
            raise

    async def async_restart_device(self, site_id: str, device_id: str) -> bool:
        """Restart a device."""
        _LOGGER.debug(
            "Attempting to restart device %s in site %s",
            device_id,
            site_id
        )
        try:
            response = await self._request(
                "POST",
                f"/v1/sites/{site_id}/devices/{device_id}/actions",
                json={"action": "RESTART"}
            )
            success = response.get("status") == "OK"
            if success:
                _LOGGER.info(
                    "Successfully initiated restart for device %s in site %s",
                    device_id,
                    site_id
                )
            else:
                _LOGGER.error(
                    "Failed to restart device %s in site %s",
                    device_id,
                    site_id
                )
            return success
        except Exception as err:
            _LOGGER.error(
                "Error restarting device %s in site %s: %s",
                device_id,
                site_id,
                err
            )
            raise

    async def async_validate_api_key(self) -> bool:
        """Validate API key by fetching sites."""
        _LOGGER.debug("Validating API key")
        try:
            await self.async_get_sites()
            _LOGGER.info("API key validation successful")
            return True
        except UnifiInsightsAuthError:
            _LOGGER.error("API key validation failed")
            return False
        except Exception as err:
            _LOGGER.error("Unexpected error during API key validation: %s", err)
            return False