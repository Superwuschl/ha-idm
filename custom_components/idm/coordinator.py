""""Data coordinator for iDM integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import IDMApi
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


_LOGGER = logging.getLogger(__name__)


class IDMDataUpdateCoordinator(DataUpdateCoordinator):
    """Manage iDM data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: IDMApi,
    ) -> None:
        """Initialize coordinator."""

        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=DEFAULT_SCAN_INTERVAL
            ),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from iDM."""

        try:
            return await self.api.get_values()

        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with iDM: {err}"
            ) from err