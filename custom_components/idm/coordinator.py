"""Data coordinator for iDM integration."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import IDMApi
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


_LOGGER = logging.getLogger(__name__)


class IDMDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching iDM data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: IDMApi,
    ):
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

    async def _async_update_data(self):
        """Fetch data from iDM."""

        try:
            return await self.api.get_values()

        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with iDM: {err}"
            ) from err