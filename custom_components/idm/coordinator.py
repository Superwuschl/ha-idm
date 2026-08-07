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


        try:
            data["heatpump"] = await self.api.heatpump()

            hp = data["heatpump"]

            _LOGGER.info(
                "iDM Status: Modell=%s ID=%s Online=%s",
                hp.get("wp_type"),
                hp.get("wp_id"),
                hp.get("online"),
            )

        except Exception as err:
            _LOGGER.error(
                "iDM heatpump API Fehler: %s",
                err,
            )


        try:
            data["graph"] = await self.api.system_graph()

        except Exception as err:
            _LOGGER.error(
                "iDM graph_system Fehler: %s",
                err,
            )


        try:
            data["heat_a"] = await self.api.heat_a_graph()

        except Exception as err:
            _LOGGER.error(
                "iDM graph_heat_a Fehler: %s",
                err,
            )


        try:
            data["heat_b"] = await self.api.heat_b_graph()

        except Exception as err:

            _LOGGER.warning(
                "iDM graph_heat_b nicht verfügbar: %s",
                err,
            )

            data["heat_b"] = {
                "data": []
            }


        return data