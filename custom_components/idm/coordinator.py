from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import IDMApi


_LOGGER = logging.getLogger(__name__)


class IDMCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Koordiniert die Daten der iDM Wärmepumpe."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: IDMApi,
    ) -> None:
        """Initialisiert den Coordinator."""

        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            name="iDM",
            update_interval=timedelta(minutes=5),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Lädt alle benötigten Daten von der iDM API."""

        _LOGGER.debug(
            "iDM COORDINATOR: Update gestartet"
        )

        try:
            # ==================================================
            # STAMMDATEN
            # ==================================================

            heatpump = await self.api.heatpump()

            _LOGGER.debug(
                "iDM COORDINATOR: heatpump geladen"
            )

            # ==================================================
            # SYSTEM
            # ==================================================

            system_graph = await self.api.system_graph(
                period="24h"
            )

            _LOGGER.debug(
                "iDM COORDINATOR: system_graph geladen"
            )

            # ==================================================
            # HEIZKREIS A
            # ==================================================

            heat_a_graph = await self.api.heat_a_graph(
                period="24h"
            )

            _LOGGER.debug(
                "iDM COORDINATOR: heat_a_graph geladen"
            )

            # --------------------------------------------------
            # HEIZKREIS-A DATEN PRÜFEN
            # --------------------------------------------------

            if isinstance(heat_a_graph, dict):

                points = heat_a_graph.get("data")

                if isinstance(points, list):

                    _LOGGER.debug(
                        "iDM COORDINATOR: "
                        "heat_a_graph Datenpunkte=%d",
                        len(points),
                    )

                    if points:

                        last_point = points[-1]

                        _LOGGER.debug(
                            "iDM COORDINATOR: "
                            "Heizkreis A letzter Datenpunkt=%s",
                            last_point,
                        )

                        if isinstance(last_point, dict):

                            value = last_point.get("130")

                            _LOGGER.debug(
                                "iDM COORDINATOR: "
                                "Kanal 130 Wert=%s",
                                value,
                            )

                            if value is not None:

                                try:
                                    mode = int(float(value))

                                    _LOGGER.debug(
                                        "iDM COORDINATOR: "
                                        "Kanal 130 Modus=%d",
                                        mode,
                                    )

                                except (
                                    TypeError,
                                    ValueError,
                                ):

                                    _LOGGER.warning(
                                        "iDM COORDINATOR: "
                                        "Kanal 130 konnte nicht "
                                        "konvertiert werden: %s",
                                        value,
                                    )

                else:

                    _LOGGER.warning(
                        "iDM COORDINATOR: "
                        "heat_a_graph enthält keine "
                        "gültige data-Liste"
                    )

            else:

                _LOGGER.warning(
                    "iDM COORDINATOR: "
                    "heat_a_graph ist kein Dictionary"
                )

            # ==================================================
            # HEIZKREIS B
            # ==================================================

            heat_b_graph = await self.api.heat_b_graph(
                period="24h"
            )

            _LOGGER.debug(
                "iDM COORDINATOR: heat_b_graph geladen"
            )

            # ==================================================
            # GESAMTDATEN
            # ==================================================

            data = {
                "heatpump": heatpump,
                "system_graph": system_graph,
                "heat_a_graph": heat_a_graph,
                "heat_b_graph": heat_b_graph,
            }

            _LOGGER.debug(
                "iDM COORDINATOR: Update erfolgreich"
            )

            return data

        except Exception as err:

            _LOGGER.error(
                "iDM COORDINATOR: Fehler beim Datenabruf: %s",
                err,
                exc_info=True,
            )

            raise UpdateFailed(
                f"Fehler beim Abrufen der iDM Daten: {err}"
            ) from err