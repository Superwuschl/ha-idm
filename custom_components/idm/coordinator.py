from __future__ import annotations

import logging

from datetime import timedelta

from homeassistant.core import HomeAssistant

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import IDMApi
from .const import NAME, DEFAULT_SCAN_INTERVAL


_LOGGER = logging.getLogger(__name__)


class IDMCoordinator(DataUpdateCoordinator):

    def __init__(
        self,
        hass: HomeAssistant,
        api: IDMApi,
    ):

        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            name=NAME,
            update_interval=timedelta(
                seconds=DEFAULT_SCAN_INTERVAL
            ),
        )


    async def _async_update_data(self):

        try:

            heatpump = await self.hass.async_add_executor_job(
                self.api.heatpump
            )


            graph = await self.hass.async_add_executor_job(
                self.api.system_graph
            )


            heat_a = await self.hass.async_add_executor_job(
                self.api.heat_a_graph
            )


            return {
                "heatpump": heatpump,
                "graph": graph,
                "heat_a": heat_a,
            }


        except Exception as err:

            raise UpdateFailed(
                f"iDM Datenfehler: {err}"
            ) from err