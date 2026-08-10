from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .coordinator import IDMCoordinator


_LOGGER = logging.getLogger(__name__)


# ============================================================
# HEIZKREIS-A-MODI
# ============================================================

MODES = {
    0: "Aus",
    1: "Zeitprogramm",
    2: "Normal",
    3: "Eco",
    4: "Manuell Heizen",
    5: "Manuell Kühlen",
}


MODE_VALUES = {
    "Aus": 0,
    "Zeitprogramm": 1,
    "Normal": 2,
    "Eco": 3,
    "Manuell Heizen": 4,
    "Manuell Kühlen": 5,
}


# ============================================================
# SELECT ENTITY
# ============================================================

class IDMHeatCircuitModeSelect(
    CoordinatorEntity[IDMCoordinator],
    SelectEntity,
):
    """Betriebsmodus von Heizkreis A."""

    _attr_has_entity_name = True
    _attr_name = "Heizkreis A Modus"
    _attr_icon = "mdi:home-thermometer"
    _attr_options = list(MODE_VALUES.keys())

    def __init__(
        self,
        coordinator: IDMCoordinator,
    ) -> None:
        """Initialisiert den Select."""

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"idm_{coordinator.api.wp_id}_heat_a_mode"
        )

        self._attr_current_option: str | None = None

        self._update_current_mode()

        _LOGGER.debug(
            "iDM Select initialer Heizkreis-A-Modus: %s",
            self._attr_current_option,
        )

    # ========================================================
    # DEVICE INFO
    # ========================================================

    @property
    def device_info(self):
        """Ordnet die Entity der iDM Wärmepumpe zu."""

        return {
            "identifiers": {
                ("idm", str(self.coordinator.api.wp_id))
            },
            "name": "iDM Wärmepumpe",
            "manufacturer": "iDM",
            "model": "TERRA S",
        }

    # ========================================================
    # CURRENT OPTION
    # ========================================================

    @property
    def current_option(self) -> str | None:
        """Aktueller Betriebsmodus."""

        return self._attr_current_option

    # ========================================================
    # COORDINATOR UPDATE
    # ========================================================

    def _handle_coordinator_update(self) -> None:
        """Verarbeitet neue Daten des Coordinators."""

        self._update_current_mode()

        super()._handle_coordinator_update()

    # ========================================================
    # AKTUELLEN MODUS ERMITTELN
    # ========================================================

    def _update_current_mode(self) -> None:
        """Ermittelt den aktuellen Modus aus Kanal 130."""

        data = self.coordinator.data

        if not isinstance(data, dict):
            _LOGGER.debug(
                "iDM Select: Keine gültigen Coordinator-Daten"
            )
            return

        heat_a = data.get("heat_a_graph")

        if not isinstance(heat_a, dict):
            _LOGGER.debug(
                "iDM Select: Keine heat_a_graph Daten"
            )
            return

        points = heat_a.get("data")

        if not isinstance(points, list) or not points:
            _LOGGER.debug(
                "iDM Select: Keine Heizkreis-A-Datenpunkte"
            )
            return

        # ----------------------------------------------------
        # Kanal 130 = Betriebsmodus Heizkreis A
        # ----------------------------------------------------

        for point in reversed(points):

            if not isinstance(point, dict):
                continue

            value = point.get("130")

            if value is None:
                continue

            try:
                mode = int(float(value))
            except (TypeError, ValueError):
                continue

            if mode not in MODES:
                continue

            option = MODES[mode]

            if self._attr_current_option != option:

                _LOGGER.debug(
                    "iDM: Heizkreis A Modus aus API: %s (%s)",
                    option,
                    mode,
                )

                self._attr_current_option = option

            return

        _LOGGER.debug(
            "iDM Select: Kein gültiger Modus in Kanal 130"
        )

    # ========================================================
    # MODUS SETZEN
    # ========================================================

    async def async_select_option(
        self,
        option: str,
    ) -> None:
        """Setzt den Betriebsmodus von Heizkreis A."""

        if option not in MODE_VALUES:
            raise ValueError(
                f"Unbekannter iDM Heizkreis-A-Modus: {option}"
            )

        value = MODE_VALUES[option]

        _LOGGER.info(
            "iDM: Setze Heizkreis A auf '%s' (%s)",
            option,
            value,
        )

        try:
            result = await self.coordinator.api.set_heat_a_mode(
                value
            )

        except Exception as err:

            _LOGGER.error(
                "iDM: Fehler beim Setzen des "
                "Heizkreis-A-Modus '%s': %s",
                option,
                err,
                exc_info=True,
            )

            raise

        _LOGGER.info(
            "iDM: Heizkreis-A-Modus erfolgreich gesetzt: %s",
            result,
        )

        # ----------------------------------------------------
        # Lokalen Zustand sofort aktualisieren
        #
        # Das Diagramm kann nach dem Schreiben noch einige
        # Sekunden den alten Wert liefern.
        # ----------------------------------------------------

        self._attr_current_option = option

        self.async_write_ha_state()


# ============================================================
# SETUP
# ============================================================

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Erstellt die iDM Select-Entities."""

    coordinator: IDMCoordinator = entry.runtime_data

    async_add_entities(
        [
            IDMHeatCircuitModeSelect(coordinator),
        ]
    )