from __future__ import annotations

import logging

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from homeassistant.core import HomeAssistant

from .api import IDMApi


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
            name="iDM TERRA S",
            update_interval=None,
        )


    async def _async_update_data(self):

        data = {}

        try:
            data["heatpump"] = self.api.heatpump()

        except Exception as err:
            _LOGGER.error(
                "Fehler heatpump API: %s",
                err,
            )


        try:
            data["graph"] = self.api.system_graph()

        except Exception as err:
            _LOGGER.error(
                "Fehler graph_system API: %s",
                err,
            )


        try:
            data["heat_a"] = self.api.heat_a_graph()

        except Exception as err:
            _LOGGER.error(
                "Fehler graph_heat_a API: %s",
                err,
            )


        try:
            data["heat_b"] = self.api.heat_b_graph()

        except Exception as err:
            _LOGGER.error(
                "Fehler graph_heat_b API: %s",
                err,
            )


        return data