from __future__ import annotations

import logging
from datetime import timedelta

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
            update_interval=timedelta(seconds=300),
        )


    async def _async_update_data(self):

        data = {}

        #
        # Hauptdaten Wärmepumpe
        #

        try:
            data["heatpump"] = self.api.heatpump()

        except Exception as err:
            _LOGGER.error(
                "iDM heatpump API Fehler: %s",
                err,
            )


        #
        # System Temperaturen
        #

        try:
            data["graph"] = self.api.system_graph()

        except Exception as err:
            _LOGGER.error(
                "iDM graph_system Fehler: %s",
                err,
            )


        #
        # Heizkreis A
        #

        try:
            data["heat_a"] = self.api.heat_a_graph()

        except Exception as err:
            _LOGGER.error(
                "iDM graph_heat_a Fehler: %s",
                err,
            )


        #
        # Heizkreis B (optional)
        #

        try:
            data["heat_b"] = self.api.heat_b_graph()

        except Exception as err:
            _LOGGER.warning(
                "iDM graph_heat_b nicht verfügbar: %s",
                err,
            )

            data["heat_b"] = {
                "data": []
            }


        return data