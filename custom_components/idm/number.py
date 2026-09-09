from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import IDMCoordinator

_LOGGER = logging.getLogger(__name__)


# ============================================================
# NAV1 READBACK
# ============================================================
#
# WICHTIG:
#
# coordinator.get_navigator_field() liefert nur den bereits
# gespeicherten Coordinator-Wert.
#
# Für die Bestätigung eines Schreibvorgangs wird deshalb hier
# direkt api.navigator_dashboard() aufgerufen.
#
# Dadurch wird nach NC_SET_PARAM ein AKTUELLER NAV1-Wert
# abgefragt.
#
# ============================================================

NAV1_READBACK_ATTEMPTS = 10
NAV1_READBACK_DELAY = 1.0
NAV1_READBACK_TOLERANCE = 0.05

# Gemeinsame Sperre für beide Number-Entities.
#
# Dadurch können nicht gleichzeitig mehrere Schreib-/Readback-
# Sequenzen laufen.
#
_NAV1_WRITE_LOCK = asyncio.Lock()


# ============================================================
# AKTIVEN NAV1-WERT LESEN
# ============================================================


async def _read_active_navigator_field(
    coordinator: IDMCoordinator,
    field: str,
) -> Any | None:
    """Liest ein Feld direkt aus dem aktuellen NAV1-Dashboard."""

    if coordinator.api is None:
        _LOGGER.error(
            "iDM NUMBER: "
            "Aktives NAV1-Readback nicht möglich: "
            "keine API-Instanz vorhanden"
        )
        return None

    try:
        dashboard = await coordinator.api.navigator_dashboard()

    except Exception as err:
        _LOGGER.error(
            "iDM NUMBER: "
            "Aktiver NAV1-Read für Feld %s fehlgeschlagen: %s",
            field,
            err,
            exc_info=True,
        )

        return None

    if not isinstance(
        dashboard,
        dict,
    ):
        _LOGGER.warning(
            "iDM NUMBER: "
            "Aktives NAV1-Dashboard ist kein Dictionary"
        )

        return None

    value = IDMCoordinator._find_nav1_field_recursive(
        dashboard,
        field,
    )

    return value


# ============================================================
# AUF NAV1 READBACK WARTEN
# ============================================================


async def _wait_for_navigator_readback(
    coordinator: IDMCoordinator,
    field: str,
    expected_value: float,
    parameter_address: int,
) -> bool:
    """Wartet auf eine tatsächliche NAV1-Bestätigung."""

    for attempt in range(
        1,
        NAV1_READBACK_ATTEMPTS + 1,
    ):
        # ----------------------------------------------------
        # Vor jedem Versuch kurz warten.
        #
        # Dadurch bekommt der Navigator Zeit, den geschriebenen
        # Parameter intern zu übernehmen.
        # ----------------------------------------------------

        await asyncio.sleep(
            NAV1_READBACK_DELAY
        )

        # ----------------------------------------------------
        # AKTIVER NAV1-READ
        #
        # NICHT coordinator.get_navigator_field() verwenden!
        # ----------------------------------------------------

        readback = await _read_active_navigator_field(
            coordinator,
            field,
        )

        _LOGGER.warning(
            "iDM NUMBER: "
            "NAV1 Readback Adresse=%d "
            "Versuch=%d/%d "
            "Feld=%s "
            "Wert=%r "
            "Erwartet=%.1f °C",
            parameter_address,
            attempt,
            NAV1_READBACK_ATTEMPTS,
            field,
            readback,
            expected_value,
        )

        if readback is None:
            continue

        try:
            numeric_readback = float(
                readback
            )

        except (
            TypeError,
            ValueError,
        ):
            _LOGGER.warning(
                "iDM NUMBER: "
                "NAV1 Readback Adresse=%d "
                "ungültiger Wert=%r",
                parameter_address,
                readback,
            )

            continue

        # ----------------------------------------------------
        # TOLERANZ
        # ----------------------------------------------------

        if abs(
            numeric_readback
            - expected_value
        ) <= NAV1_READBACK_TOLERANCE:
            _LOGGER.warning(
                "iDM NUMBER: "
                "NAV1 READBACK BESTÄTIGT: "
                "Adresse=%d "
                "Feld=%s "
                "Wert=%.1f °C",
                parameter_address,
                field,
                numeric_readback,
            )

            return True

    # --------------------------------------------------------
    # KEINE BESTÄTIGUNG
    # --------------------------------------------------------

    _LOGGER.error(
        "iDM NUMBER: "
        "NAV1 READBACK NICHT BESTÄTIGT: "
        "Adresse=%d "
        "Feld=%s "
        "Erwartet=%.1f °C "
        "nach %d Versuchen",
        parameter_address,
        field,
        expected_value,
        NAV1_READBACK_ATTEMPTS,
    )

    return False


# ============================================================
# HEIZKREIS A – NORMALTEMPERATUR
# ============================================================


class IDMHeatCircuitNormalTemperatureNumber(
    CoordinatorEntity[IDMCoordinator],
    NumberEntity,
):
    """Normale Raum-Solltemperatur von Heizkreis A."""

    _attr_has_entity_name = True
    _attr_name = "Heizkreis A Normaltemperatur"
    _attr_icon = "mdi:home-thermometer"
    _attr_native_min_value = 15.0
    _attr_native_max_value = 30.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = "slider"

    def __init__(
        self,
        coordinator: IDMCoordinator,
    ) -> None:
        """Initialisiert die Normaltemperatur."""

        super().__init__(
            coordinator
        )

        self._attr_unique_id = (
            f"idm_{coordinator.api.wp_id}_"
            "heat_a_normal_temperature"
        )

        self._attr_native_value: float | None = None

        self._commanded_value: float | None = None

        self._update_value()

        _LOGGER.debug(
            "iDM Number: Initiale Heizkreis-A "
            "Normaltemperatur: %s °C",
            self._attr_native_value,
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
    # COORDINATOR UPDATE
    # ========================================================

    def _handle_coordinator_update(self) -> None:
        """Verarbeitet neue Daten des Coordinators."""

        self._update_value()

        super()._handle_coordinator_update()

    # ========================================================
    # AKTUELLEN WERT ERMITTELN
    # ========================================================

    def _update_value(self) -> None:
        """Ermittelt die aktuelle Normaltemperatur."""

        if self._commanded_value is not None:
            self._attr_native_value = (
                self._commanded_value
            )

            return

        value = self.coordinator.get_navigator_field(
            "circuit_temp_normal"
        )

        if value is None:
            _LOGGER.debug(
                "iDM Number: "
                "Navigator-Feld circuit_temp_normal "
                "nicht vorhanden"
            )

            return

        try:
            numeric_value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            _LOGGER.debug(
                "iDM Number: "
                "Ungültiger Normaltemperatur-Wert: %r",
                value,
            )

            return

        self._attr_native_value = numeric_value

    # ========================================================
    # WERT SETZEN
    # ========================================================

    async def async_set_native_value(
        self,
        value: float,
    ) -> None:
        """Setzt die normale Raum-Solltemperatur."""

        value = float(value)

        # ----------------------------------------------------
        # GESAMTEN WRITE/READBACK-VORGANG SERIALISIEREN
        # ----------------------------------------------------

        async with _NAV1_WRITE_LOCK:
            _LOGGER.warning(
                "iDM NUMBER: "
                "Setze Heizkreis A Normaltemperatur "
                "Adresse=2016 auf %.1f °C",
                value,
            )

            # ------------------------------------------------
            # WRITE
            # ------------------------------------------------

            try:
                result = await (
                    self.coordinator.api
                    .set_heat_a_normal_temperature(
                        value
                    )
                )

            except Exception as err:
                _LOGGER.error(
                    "iDM NUMBER: "
                    "Fehler beim Setzen der "
                    "Normaltemperatur %.1f °C: %s",
                    value,
                    err,
                    exc_info=True,
                )

                raise

            _LOGGER.warning(
                "iDM NUMBER: "
                "NC_SET_PARAM Adresse=2016 "
                "Antwort=%s",
                result,
            )

            # ------------------------------------------------
            # AKTIVES NAV1 READBACK
            # ------------------------------------------------

            confirmed = await (
                _wait_for_navigator_readback(
                    coordinator=self.coordinator,
                    field="circuit_temp_normal",
                    expected_value=value,
                    parameter_address=2016,
                )
            )

            # ------------------------------------------------
            # BESTÄTIGT
            # ------------------------------------------------

            if confirmed:
                self._attr_native_value = value

                # ------------------------------------------------
                # WICHTIG:
                # Nach erfolgreicher NAV1-Bestätigung darf der
                # Command nicht dauerhaft als Datenquelle
                # gespeichert bleiben.
                #
                # Künftige Coordinator-Updates sollen wieder
                # den tatsächlichen NAV1-Wert übernehmen.
                # ------------------------------------------------

                self._commanded_value = None

                _LOGGER.warning(
                    "iDM NUMBER: "
                    "Normaltemperatur Adresse=2016 "
                    "%.1f °C durch NAV1 bestätigt",
                    value,
                )

            # ------------------------------------------------
            # NICHT BESTÄTIGT
            # ------------------------------------------------
            #
            # KEIN RuntimeError!
            #
            # Der Schreibvorgang wurde von NC_SET_PARAM
            # bereits mit status=ok quittiert.
            #
            # Wir behaupten aber nicht, dass der Navigator
            # den Wert übernommen hat.
            #
            else:
                self._commanded_value = None

                self._update_value()

                _LOGGER.warning(
                    "iDM NUMBER: "
                    "Adresse=2016 wurde mit status=ok "
                    "geschrieben, aber NAV1 konnte den Wert "
                    "%.1f °C nicht bestätigen",
                    value,
                )

            self.async_write_ha_state()


# ============================================================
# HEIZKREIS A – ECO-TEMPERATUR
# ============================================================


class IDMHeatCircuitEcoTemperatureNumber(
    CoordinatorEntity[IDMCoordinator],
    NumberEntity,
):
    """Eco-Raum-Solltemperatur von Heizkreis A."""

    _attr_has_entity_name = True
    _attr_name = "Heizkreis A Eco-Temperatur"
    _attr_icon = "mdi:home-thermometer-outline"
    _attr_native_min_value = 10.0
    _attr_native_max_value = 25.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = "slider"

    def __init__(
        self,
        coordinator: IDMCoordinator,
    ) -> None:
        """Initialisiert die Eco-Temperatur."""

        super().__init__(
            coordinator
        )

        self._attr_unique_id = (
            f"idm_{coordinator.api.wp_id}_"
            "heat_a_eco_temperature"
        )

        self._attr_native_value: float | None = None

        self._commanded_value: float | None = None

        self._update_value()

        _LOGGER.debug(
            "iDM Number: Initiale Heizkreis-A "
            "Eco-Temperatur: %s °C",
            self._attr_native_value,
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
    # COORDINATOR UPDATE
    # ========================================================

    def _handle_coordinator_update(self) -> None:
        """Verarbeitet neue Daten des Coordinators."""

        self._update_value()

        super()._handle_coordinator_update()

    # ========================================================
    # AKTUELLEN WERT ERMITTELN
    # ========================================================

    def _update_value(self) -> None:
        """Ermittelt die aktuelle Eco-Temperatur."""

        if self._commanded_value is not None:
            self._attr_native_value = (
                self._commanded_value
            )

            return

        value = self.coordinator.get_navigator_field(
            "circuit_temp_eco"
        )

        if value is None:
            _LOGGER.debug(
                "iDM Number: "
                "Navigator-Feld circuit_temp_eco "
                "nicht vorhanden"
            )

            return

        try:
            numeric_value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            _LOGGER.debug(
                "iDM Number: "
                "Ungültiger Eco-Temperatur-Wert: %r",
                value,
            )

            return

        self._attr_native_value = numeric_value

    # ========================================================
    # WERT SETZEN
    # ========================================================

    async def async_set_native_value(
        self,
        value: float,
    ) -> None:
        """Setzt die Eco-Raum-Solltemperatur."""

        value = float(value)

        async with _NAV1_WRITE_LOCK:
            _LOGGER.warning(
                "iDM NUMBER: "
                "Setze Heizkreis A Eco-Temperatur "
                "Adresse=2030 auf %.1f °C",
                value,
            )

            # ------------------------------------------------
            # WRITE
            # ------------------------------------------------

            try:
                result = await (
                    self.coordinator.api
                    .set_heat_a_eco_temperature(
                        value
                    )
                )

            except Exception as err:
                _LOGGER.error(
                    "iDM NUMBER: "
                    "Fehler beim Setzen der "
                    "Eco-Temperatur %.1f °C: %s",
                    value,
                    err,
                    exc_info=True,
                )

                raise

            _LOGGER.warning(
                "iDM NUMBER: "
                "NC_SET_PARAM Adresse=2030 "
                "Antwort=%s",
                result,
            )

            # ------------------------------------------------
            # AKTIVES NAV1 READBACK
            # ------------------------------------------------

            confirmed = await (
                _wait_for_navigator_readback(
                    coordinator=self.coordinator,
                    field="circuit_temp_eco",
                    expected_value=value,
                    parameter_address=2030,
                )
            )

            # ------------------------------------------------
            # BESTÄTIGT
            # ------------------------------------------------

            if confirmed:
                self._attr_native_value = value

                # ------------------------------------------------
                # WICHTIG:
                # Nach erfolgreicher NAV1-Bestätigung darf der
                # Command nicht dauerhaft als Datenquelle
                # gespeichert bleiben.
                #
                # Künftige Coordinator-Updates sollen wieder
                # den tatsächlichen NAV1-Wert übernehmen.
                # ------------------------------------------------

                self._commanded_value = None

                _LOGGER.warning(
                    "iDM NUMBER: "
                    "Eco-Temperatur Adresse=2030 "
                    "%.1f °C durch NAV1 bestätigt",
                    value,
                )

            # ------------------------------------------------
            # NICHT BESTÄTIGT
            # ------------------------------------------------

            else:
                self._commanded_value = None

                self._update_value()

                _LOGGER.warning(
                    "iDM NUMBER: "
                    "Adresse=2030 wurde mit status=ok "
                    "geschrieben, aber NAV1 konnte den Wert "
                    "%.1f °C nicht bestätigen",
                    value,
                )

            self.async_write_ha_state()


# ============================================================
# SETUP
# ============================================================


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Erstellt die iDM Number-Entities."""

    coordinator: IDMCoordinator = entry.runtime_data

    _LOGGER.debug(
        "iDM NUMBER: Setup gestartet"
    )

    async_add_entities(
        [
            IDMHeatCircuitNormalTemperatureNumber(
                coordinator
            ),
            IDMHeatCircuitEcoTemperatureNumber(
                coordinator
            ),
        ]
    )

    _LOGGER.debug(
        "iDM NUMBER: "
        "Normal- und Eco-Temperatur "
        "Entities erstellt"
    )