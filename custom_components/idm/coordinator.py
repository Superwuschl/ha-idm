from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .modbus import IDMModbus


_LOGGER = logging.getLogger(__name__)


# ============================================================================
# iDM COORDINATOR
# ============================================================================
#
# Datenquellen:
#
#   1. Modbus TCP
#      - primäre Datenquelle
#      - READ ONLY
#      - kein Token erforderlich
#
#   2. myIDM Cloud API
#      - optional
#      - nur aktiv, wenn eine API-Instanz vorhanden ist
#
#   3. Navigator NAV1 Dashboard
#      - zyklisch über myIDM API
#      - liefert die aktuellen Navigator-Werte
#      - wird von select.py und number.py verwendet
#
# ============================================================================


class IDMCoordinator(
    DataUpdateCoordinator[dict[str, Any]]
):
    """Koordiniert myIDM und iDM Modbus TCP."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: Any | None = None,
        modbus: IDMModbus | None = None,
    ) -> None:
        """Initialisiert den Coordinator."""

        self.api = api
        self.modbus = modbus

        super().__init__(
            hass,
            _LOGGER,
            name="iDM",
            update_interval=timedelta(
                minutes=5
            ),
        )

    # =========================================================================
    # UPDATE
    # =========================================================================

    async def _async_update_data(
        self,
    ) -> dict[str, Any]:
        """Lädt alle verfügbaren iDM-Daten."""

        _LOGGER.debug(
            "iDM COORDINATOR: Update gestartet"
        )

        data: dict[str, Any] = {}

        # =====================================================================
        # MYIDM
        # =====================================================================

        if self.api is not None:
            await self._update_myidm(
                data
            )
        else:
            _LOGGER.debug(
                "iDM COORDINATOR: "
                "myIDM API nicht konfiguriert"
            )

        # =====================================================================
        # MODBUS
        # =====================================================================

        await self._update_modbus(
            data
        )

        # =====================================================================
        # ABSCHLUSS
        # =====================================================================

        if not data:
            raise UpdateFailed(
                "Keine iDM Daten konnten geladen werden."
            )

        _LOGGER.debug(
            "iDM COORDINATOR: Update erfolgreich"
        )

        return data

    # =========================================================================
    # MYIDM
    # =========================================================================

    async def _update_myidm(
        self,
        data: dict[str, Any],
    ) -> None:
        """Lädt Daten aus der optionalen myIDM Cloud API."""

        if self.api is None:
            return

        # ---------------------------------------------------------------------
        # STAMMDATEN
        # ---------------------------------------------------------------------

        try:
            heatpump = await self.api.heatpump()

            if isinstance(
                heatpump,
                dict,
            ):
                data["heatpump"] = heatpump
            else:
                data["heatpump"] = {}

            _LOGGER.debug(
                "iDM COORDINATOR: heatpump geladen"
            )

        except Exception as err:
            _LOGGER.error(
                "iDM COORDINATOR: "
                "heatpump konnte nicht geladen werden: %s",
                err,
                exc_info=True,
            )

            data["heatpump"] = {}

        # ---------------------------------------------------------------------
        # SYSTEM
        # ---------------------------------------------------------------------

        try:
            system_graph = (
                await self.api.system_graph(
                    period="24h"
                )
            )

            data["system_graph"] = (
                system_graph
                if isinstance(
                    system_graph,
                    dict,
                )
                else {}
            )

            _LOGGER.debug(
                "iDM COORDINATOR: system_graph geladen"
            )

        except Exception as err:
            _LOGGER.error(
                "iDM COORDINATOR: "
                "system_graph konnte nicht geladen werden: %s",
                err,
                exc_info=True,
            )

            data["system_graph"] = {}

        # ---------------------------------------------------------------------
        # HEIZKREIS A
        # ---------------------------------------------------------------------

        try:
            heat_a_graph = (
                await self.api.heat_a_graph(
                    period="24h"
                )
            )

            data["heat_a_graph"] = (
                heat_a_graph
                if isinstance(
                    heat_a_graph,
                    dict,
                )
                else {}
            )

            _LOGGER.debug(
                "iDM COORDINATOR: heat_a_graph geladen"
            )

            self._log_heat_a_channel_130(
                heat_a_graph
            )

        except Exception as err:
            _LOGGER.error(
                "iDM COORDINATOR: "
                "heat_a_graph konnte nicht geladen werden: %s",
                err,
                exc_info=True,
            )

            data["heat_a_graph"] = {}

        # ---------------------------------------------------------------------
        # HEIZKREIS B
        # ---------------------------------------------------------------------

        try:
            heat_b_graph = (
                await self.api.heat_b_graph(
                    period="24h"
                )
            )

            data["heat_b_graph"] = (
                heat_b_graph
                if isinstance(
                    heat_b_graph,
                    dict,
                )
                else {}
            )

            _LOGGER.debug(
                "iDM COORDINATOR: heat_b_graph geladen"
            )

        except Exception as err:
            _LOGGER.error(
                "iDM COORDINATOR: "
                "heat_b_graph konnte nicht geladen werden: %s",
                err,
                exc_info=True,
            )

            data["heat_b_graph"] = {}

        # ---------------------------------------------------------------------
        # NAVIGATOR NAV1 DASHBOARD
        # ---------------------------------------------------------------------

        try:
            navigator_dashboard = (
                await self.api.navigator_dashboard()
            )

            data["navigator_dashboard"] = (
                navigator_dashboard
                if isinstance(
                    navigator_dashboard,
                    dict,
                )
                else {}
            )

            _LOGGER.debug(
                "iDM COORDINATOR: "
                "navigator_dashboard geladen"
            )

            # ================================================================
            # NAV1 WERTE
            # ================================================================
            #
            # Die NAV1-Struktur enthält:
            #
            #   sections[]
            #       info
            #       hygienic
            #       circuits
            #           sections[]
            #               Heating Circuit A
            #                   fields[]
            #
            # Deshalb werden die Felder rekursiv gesucht.
            #
            # ================================================================

            nav1_values: dict[str, Any] = {
                "system_mode": None,
                "circuit_mode": None,
                "circuit_temp_normal": None,
                "circuit_temp_eco": None,
            }

            dashboard = data[
                "navigator_dashboard"
            ]

            if isinstance(
                dashboard,
                dict,
            ):

                for key in nav1_values:
                    value = (
                        self._find_nav1_field_recursive(
                            dashboard,
                            key,
                        )
                    )

                    if value is not None:
                        nav1_values[
                            key
                        ] = value

            # ================================================================
            # NAV1 WERTE IM COORDINATOR SPEICHERN
            # ================================================================

            data[
                "navigator_values"
            ] = dict(
                nav1_values
            )

            # ================================================================
            # KONZISE NAV1-ZUSAMMENFASSUNG
            # ================================================================
            #
            # TEMPÄR WARNING:
            # Damit der NAV1-Read im normalen HA-Log sichtbar ist.
            #
            # ================================================================

            _LOGGER.warning(
                "iDM NAV1 READ: "
                "system_mode=%s | "
                "circuit_mode=%s | "
                "circuit_temp_normal=%s °C | "
                "circuit_temp_eco=%s °C",
                nav1_values[
                    "system_mode"
                ],
                nav1_values[
                    "circuit_mode"
                ],
                nav1_values[
                    "circuit_temp_normal"
                ],
                nav1_values[
                    "circuit_temp_eco"
                ],
            )

        except Exception as err:
            _LOGGER.error(
                "iDM COORDINATOR: "
                "navigator_dashboard konnte nicht geladen werden: %s",
                err,
                exc_info=True,
            )

            data["navigator_dashboard"] = {}

            data[
                "navigator_values"
            ] = {
                "system_mode": None,
                "circuit_mode": None,
                "circuit_temp_normal": None,
                "circuit_temp_eco": None,
            }

    # =========================================================================
    # NAV1 FELDSUCHE
    # =========================================================================

    @staticmethod
    def _find_nav1_field_recursive(
        value: Any,
        key: str,
        depth: int = 0,
    ) -> Any | None:
        """
        Sucht rekursiv nach einem NAV1-Feld mit dem angegebenen key.

        Unterstützt:
          - normale sections[].fields[]
          - circuits.sections[].fields[]
          - beliebig verschachtelte NAV1-Strukturen

        Beispiel:

            circuits
                sections[0]
                    fields[3]
                        key = circuit_mode
                        value = 2
        """

        # Schutz gegen unerwartet tiefe Strukturen.
        if depth > 20:
            return None

        # ---------------------------------------------------------------------
        # DICT
        # ---------------------------------------------------------------------

        if isinstance(
            value,
            dict,
        ):

            # Exaktes NAV1-Feld gefunden.
            if (
                value.get("key") == key
                and "value" in value
            ):
                return value.get(
                    "value"
                )

            # Alle Unterelemente durchsuchen.
            for child in value.values():

                result = (
                    IDMCoordinator._find_nav1_field_recursive(
                        child,
                        key,
                        depth + 1,
                    )
                )

                if result is not None:
                    return result

            return None

        # ---------------------------------------------------------------------
        # LIST
        # ---------------------------------------------------------------------

        if isinstance(
            value,
            list,
        ):

            for child in value:

                result = (
                    IDMCoordinator._find_nav1_field_recursive(
                        child,
                        key,
                        depth + 1,
                    )
                )

                if result is not None:
                    return result

            return None

        # ---------------------------------------------------------------------
        # PRIMITIVE
        # ---------------------------------------------------------------------

        return None

    # =========================================================================
    # NAVIGATOR DASHBOARD
    # =========================================================================

    def get_navigator_field(
        self,
        key: str,
    ) -> Any | None:
        """
        Liefert den Wert eines Feldes aus dem NAV1-Dashboard.

        Unterstützt:
          - normale sections[].fields[]
          - verschachtelte circuits.sections[].fields[]
          - weitere verschachtelte NAV1-Strukturen
        """

        if not self.data:
            return None

        dashboard = self.data.get(
            "navigator_dashboard",
            {},
        )

        if not isinstance(
            dashboard,
            dict,
        ):
            return None

        # ---------------------------------------------------------------------
        # 1. Zuerst gespeicherte NAV1-Werte verwenden.
        # ---------------------------------------------------------------------

        navigator_values = self.data.get(
            "navigator_values",
            {},
        )

        if isinstance(
            navigator_values,
            dict,
        ):

            if key in navigator_values:

                value = navigator_values.get(
                    key
                )

                if value is not None:

                    _LOGGER.debug(
                        "iDM COORDINATOR: "
                        "Navigator-Wert %s=%s",
                        key,
                        value,
                    )

                    return value

        # ---------------------------------------------------------------------
        # 2. Fallback: komplettes Dashboard rekursiv durchsuchen.
        # ---------------------------------------------------------------------

        value = (
            self._find_nav1_field_recursive(
                dashboard,
                key,
            )
        )

        if value is not None:

            _LOGGER.debug(
                "iDM COORDINATOR: "
                "Navigator-Feld %s=%s",
                key,
                value,
            )

            return value

        _LOGGER.debug(
            "iDM COORDINATOR: "
            "Navigator-Feld %s nicht gefunden",
            key,
        )

        return None

    # =========================================================================
    # HEIZKREIS-A DIAGNOSE
    # =========================================================================

    @staticmethod
    def _log_heat_a_channel_130(
        heat_a_graph: Any,
    ) -> None:
        """Protokolliert den letzten Wert von Kanal 130."""

        if not isinstance(
            heat_a_graph,
            dict,
        ):
            return

        points = heat_a_graph.get(
            "data"
        )

        if not isinstance(
            points,
            list,
        ):
            return

        _LOGGER.debug(
            "iDM COORDINATOR: "
            "heat_a_graph Datenpunkte=%d",
            len(points),
        )

        if not points:
            return

        for point in reversed(
            points
        ):

            if not isinstance(
                point,
                dict,
            ):
                continue

            if "130" not in point:
                continue

            value = point.get(
                "130"
            )

            if value is None:
                continue

            _LOGGER.debug(
                "iDM COORDINATOR: "
                "Heizkreis A Kanal 130 Rohwert=%s",
                value,
            )

            try:

                mode = int(
                    round(
                        float(value)
                    )
                )

                _LOGGER.debug(
                    "iDM COORDINATOR: "
                    "Heizkreis A Kanal 130 gerundet=%d",
                    mode,
                )

            except (
                TypeError,
                ValueError,
            ):

                _LOGGER.warning(
                    "iDM COORDINATOR: "
                    "Kanal 130 konnte nicht konvertiert werden: %s",
                    value,
                )

            return

        _LOGGER.debug(
            "iDM COORDINATOR: "
            "Kanal 130 wurde in heat_a_graph nicht gefunden"
        )

    # =========================================================================
    # MODBUS
    # =========================================================================

    async def _update_modbus(
        self,
        data: dict[str, Any],
    ) -> None:
        """Lädt die Modbus-Daten."""

        empty_modbus = {
            "available": False,
            "sensors": {},
            "status": {},
            "parameters": {},
        }

        # ---------------------------------------------------------------------
        # NICHT KONFIGURIERT
        # ---------------------------------------------------------------------

        if self.modbus is None:

            _LOGGER.debug(
                "iDM COORDINATOR: "
                "Modbus ist nicht konfiguriert"
            )

            data["modbus"] = empty_modbus

            return

        # ---------------------------------------------------------------------
        # VERBINDUNG
        # ---------------------------------------------------------------------

        try:

            if not self.modbus.client.connected:

                _LOGGER.debug(
                    "iDM COORDINATOR: "
                    "Modbus nicht verbunden - verbinde..."
                )

                connected = (
                    await self.modbus.async_connect()
                )

                if not connected:

                    _LOGGER.warning(
                        "iDM COORDINATOR: "
                        "Modbus-Verbindung konnte nicht hergestellt werden"
                    )

                    data["modbus"] = empty_modbus

                    return

        except Exception as err:

            _LOGGER.error(
                "iDM COORDINATOR: "
                "Modbus-Verbindung fehlgeschlagen: %s",
                err,
                exc_info=True,
            )

            data["modbus"] = empty_modbus

            return

        # ---------------------------------------------------------------------
        # SENSORWERTE
        # ---------------------------------------------------------------------

        sensors: dict[str, Any] = {}

        try:

            sensors = (
                await self.modbus.read_all_sensors()
            )

            _LOGGER.debug(
                "iDM COORDINATOR: "
                "Modbus Sensoren geladen: %d",
                len(sensors),
            )

        except Exception as err:

            _LOGGER.error(
                "iDM COORDINATOR: "
                "Modbus Sensoren konnten nicht geladen werden: %s",
                err,
                exc_info=True,
            )

        # ---------------------------------------------------------------------
        # STATUS
        # ---------------------------------------------------------------------

        status: dict[str, Any] = {}

        try:

            status = (
                await self.modbus.read_all_status()
            )

            _LOGGER.debug(
                "iDM COORDINATOR: "
                "Modbus Status geladen: %d",
                len(status),
            )

        except Exception as err:

            _LOGGER.error(
                "iDM COORDINATOR: "
                "Modbus Status konnte nicht geladen werden: %s",
                err,
                exc_info=True,
            )

        # ---------------------------------------------------------------------
        # PARAMETER
        # ---------------------------------------------------------------------

        parameters: dict[str, Any] = {}

        try:

            parameters = (
                await self.modbus.read_all_parameters()
            )

            _LOGGER.debug(
                "iDM COORDINATOR: "
                "Modbus Parameter geladen: %d",
                len(parameters),
            )

        except Exception as err:

            _LOGGER.error(
                "iDM COORDINATOR: "
                "Modbus Parameter konnten nicht geladen werden: %s",
                err,
                exc_info=True,
            )

        # ---------------------------------------------------------------------
        # DATEN ZUSAMMENFASSEN
        # ---------------------------------------------------------------------

        available = bool(
            sensors
            or status
            or parameters
        )

        data["modbus"] = {
            "available": available,
            "sensors": sensors,
            "status": status,
            "parameters": parameters,
        }

        _LOGGER.debug(
            "iDM COORDINATOR: "
            "Modbus Update abgeschlossen "
            "(available=%s, Sensoren=%d, Status=%d, Parameter=%d)",
            available,
            len(sensors),
            len(status),
            len(parameters),
        )

    # =========================================================================
    # MODBUS STATUS
    # =========================================================================

    @property
    def modbus_available(
        self,
    ) -> bool:
        """Liefert den Modbus-Verfügbarkeitsstatus."""

        if not self.data:
            return False

        modbus_data = self.data.get(
            "modbus",
            {},
        )

        if not isinstance(
            modbus_data,
            dict,
        ):
            return False

        return bool(
            modbus_data.get(
                "available",
                False,
            )
        )

    # =========================================================================
    # MODBUS SENSOR
    # =========================================================================

    def get_modbus_sensor(
        self,
        key: str,
    ) -> dict[str, Any] | None:
        """Liefert einen einzelnen Modbus-Sensor."""

        modbus_data = self._get_modbus_data()

        if modbus_data is None:
            return None

        sensors = modbus_data.get(
            "sensors",
            {},
        )

        if not isinstance(
            sensors,
            dict,
        ):
            return None

        value = sensors.get(
            key
        )

        if not isinstance(
            value,
            dict,
        ):
            return None

        return value

    # =========================================================================
    # MODBUS STATUS
    # =========================================================================

    def get_modbus_status(
        self,
        key: str,
    ) -> dict[str, Any] | None:
        """Liefert einen einzelnen Modbus-Status."""

        modbus_data = self._get_modbus_data()

        if modbus_data is None:
            return None

        status = modbus_data.get(
            "status",
            {},
        )

        if not isinstance(
            status,
            dict,
        ):
            return None

        value = status.get(
            key
        )

        if not isinstance(
            value,
            dict,
        ):
            return None

        return value

    # =========================================================================
    # MODBUS PARAMETER
    # =========================================================================

    def get_modbus_parameter(
        self,
        key: str,
    ) -> dict[str, Any] | None:
        """Liefert einen einzelnen Modbus-Parameter."""

        modbus_data = self._get_modbus_data()

        if modbus_data is None:
            return None

        parameters = modbus_data.get(
            "parameters",
            {},
        )

        if not isinstance(
            parameters,
            dict,
        ):
            return None

        value = parameters.get(
            key
        )

        if not isinstance(
            value,
            dict,
        ):
            return None

        return value

    # =========================================================================
    # MODBUS DATEN INTERN
    # =========================================================================

    def _get_modbus_data(
        self,
    ) -> dict[str, Any] | None:
        """Liefert den kompletten Modbus-Datenblock."""

        if not self.data:
            return None

        modbus_data = self.data.get(
            "modbus",
            {},
        )

        if not isinstance(
            modbus_data,
            dict,
        ):
            return None

        return modbus_data

    # =========================================================================
    # SHUTDOWN
    # =========================================================================

    async def async_shutdown(
        self,
    ) -> None:
        """Beendet den Coordinator und schließt Modbus und myIDM API."""

        _LOGGER.debug(
            "iDM COORDINATOR: Shutdown"
        )

        # ---------------------------------------------------------------------
        # MODBUS SCHLIESSEN
        # ---------------------------------------------------------------------

        if self.modbus is not None:

            try:

                await self.modbus.async_close()

            except Exception:

                _LOGGER.exception(
                    "iDM COORDINATOR: "
                    "Fehler beim Schließen von Modbus"
                )

        # ---------------------------------------------------------------------
        # MYIDM API / AIOHTTP SESSION SCHLIESSEN
        # ---------------------------------------------------------------------

        if self.api is not None:

            try:

                await self.api.close()

            except Exception:

                _LOGGER.exception(
                    "iDM COORDINATOR: "
                    "Fehler beim Schließen der myIDM API"
                )