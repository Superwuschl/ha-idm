from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


# ============================================================================
# iDM SENSOR
# ============================================================================
#
# Diese Datei verwendet ausschließlich die aktuellen Modbus-Daten aus:
#
# coordinator.data["modbus"]
#
# Erwartete Struktur:
#
# {
#     "modbus": {
#         "sensors": {...},
#         "status": {...},
#         "parameters": {...},
#     }
# }
#
# Die alten myIDM-Diagramm- und Stammdatensensoren werden bewusst nicht mehr
# erzeugt. Dadurch verschwinden die bisherigen "Unbekannt"- und Doppelwerte.
#
# Heizkreis:
#   Es wird nur Heizkreis A verwendet.
#
# ============================================================================


# ============================================================================
# GERÄTEINFORMATION
# ============================================================================


def _get_device_info(
    coordinator: Any,
) -> DeviceInfo:
    """Erstellt die gemeinsame Geräteinformation."""

    heatpump: dict[str, Any] = {}

    if coordinator.data:
        heatpump = coordinator.data.get(
            "heatpump",
            {},
        )

    if not isinstance(heatpump, dict):
        heatpump = {}

    wp_id = heatpump.get("wp_id")
    serialnumber = heatpump.get("serialnumber")
    wp_type = heatpump.get("wp_type")
    name = heatpump.get("name")

    # ------------------------------------------------------------------------
    # Seriennummer
    # ------------------------------------------------------------------------

    if serialnumber is not None:
        serial = str(serialnumber)

    elif wp_id is not None:
        serial = str(wp_id)

    else:
        serial = "unknown"

    # ------------------------------------------------------------------------
    # Gerätename
    # ------------------------------------------------------------------------

    if name:
        device_name = str(name)

    elif wp_type:
        device_name = f"iDM {wp_type}"

    else:
        device_name = "iDM Wärmepumpe"

    # ------------------------------------------------------------------------
    # Identifier
    # ------------------------------------------------------------------------

    if wp_id is not None:
        identifier = str(wp_id)

    else:
        identifier = serial

    return DeviceInfo(
        identifiers={
            (DOMAIN, identifier),
        },
        name=device_name,
        manufacturer="iDM",
        model=str(wp_type) if wp_type else None,
        serial_number=serial,
    )


# ============================================================================
# MODBUS SENSOR
# ============================================================================


class IDMModbusSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """Dynamischer Home-Assistant-Sensor für iDM Modbus-Daten."""

    def __init__(
        self,
        coordinator: Any,
        category: str,
        key: str,
        data: dict[str, Any],
    ) -> None:
        """Initialisiert einen Modbus-Sensor."""

        super().__init__(coordinator)

        self.category = category
        self.key = key

        self._name = str(
            data.get(
                "name",
                key,
            )
        )

        self.address = data.get(
            "address"
        )

        self.function_code = data.get(
            "fc"
        )

        self.datatype = data.get(
            "datatype"
        )

        self.unit = data.get(
            "unit"
        )

        # --------------------------------------------------------------------
        # Name
        # --------------------------------------------------------------------

        self._attr_name = self._name

        # --------------------------------------------------------------------
        # Unique ID
        # --------------------------------------------------------------------

        self._attr_unique_id = (
            f"{DOMAIN}_modbus_"
            f"{category}_"
            f"{self.address}"
        )

        self._attr_has_entity_name = False

        # --------------------------------------------------------------------
        # Einheit
        # --------------------------------------------------------------------

        self._attr_native_unit_of_measurement = (
            self.unit
        )

        # --------------------------------------------------------------------
        # Device Class
        # --------------------------------------------------------------------

        self._attr_device_class = (
            self._get_device_class(
                self.unit
            )
        )

    # =========================================================================
    # DEVICE INFO
    # =========================================================================

    @property
    def device_info(self) -> DeviceInfo:
        """Liefert die gemeinsame iDM Geräteinformation."""

        return _get_device_info(
            self.coordinator
        )

    # =========================================================================
    # DEVICE CLASS
    # =========================================================================

    @staticmethod
    def _get_device_class(
        unit: str | None,
    ) -> SensorDeviceClass | None:
        """Bestimmt die passende Home-Assistant Device Class."""

        if unit == "°C":
            return SensorDeviceClass.TEMPERATURE

        if unit == "%":
            return SensorDeviceClass.HUMIDITY

        if unit == "kW":
            return SensorDeviceClass.POWER

        if unit == "kWh":
            return SensorDeviceClass.ENERGY

        return None

    # =========================================================================
    # DATEN HOLEN
    # =========================================================================

    def _get_data(
        self,
    ) -> dict[str, Any] | None:
        """Liefert den aktuellen Datensatz."""

        if not self.coordinator.data:
            return None

        modbus = self.coordinator.data.get(
            "modbus",
            {},
        )

        if not isinstance(modbus, dict):
            return None

        category_data = modbus.get(
            self.category,
            {},
        )

        if not isinstance(category_data, dict):
            return None

        value = category_data.get(
            self.key
        )

        if not isinstance(value, dict):
            return None

        return value

    # =========================================================================
    # WERT
    # =========================================================================

    @property
    def native_value(self) -> Any:
        """Liefert den aktuellen Modbus-Wert."""

        data = self._get_data()

        if data is None:
            return None

        value = data.get(
            "value"
        )

        if value is None:
            return None

        # --------------------------------------------------------------------
        # FLOAT
        # --------------------------------------------------------------------

        if isinstance(value, float):
            return round(
                value,
                2,
            )

        # --------------------------------------------------------------------
        # INTEGER
        # --------------------------------------------------------------------

        if isinstance(value, int):
            return value

        # --------------------------------------------------------------------
        # NUMERISCHER STRING
        # --------------------------------------------------------------------

        if isinstance(value, str):

            try:
                numeric_value = float(value)

            except ValueError:
                return value

            return round(
                numeric_value,
                2,
            )

        return value

    # =========================================================================
    # ATTRIBUTES
    # =========================================================================

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Liefert Modbus-Metadaten."""

        data = self._get_data()

        if data is None:
            data = {}

        return {
            "Modbus Kategorie": self.category,
            "Modbus Adresse": self.address,
            "Function Code": self.function_code,
            "Datentyp": self.datatype,
            "Einheit": self.unit,
            "Modbus Key": self.key,
        }


# ============================================================================
# SETUP
# ============================================================================


async def async_setup_entry(
    hass: Any,
    entry: Any,
    async_add_entities,
) -> None:
    """Erstellt die iDM Modbus Sensoren."""

    coordinator = entry.runtime_data

    entities: list[SensorEntity] = []

    # =========================================================================
    # MODBUS DATEN
    # =========================================================================

    modbus_data: dict[str, Any] = {}

    if coordinator.data:
        modbus_data = coordinator.data.get(
            "modbus",
            {}
        )

    if not isinstance(modbus_data, dict):
        modbus_data = {}

    # =========================================================================
    # FC04 SENSORWERTE
    # =========================================================================

    modbus_sensors = modbus_data.get(
        "sensors",
        {}
    )

    if isinstance(modbus_sensors, dict):

        for key, value in modbus_sensors.items():

            if not isinstance(value, dict):
                continue

            entities.append(
                IDMModbusSensor(
                    coordinator=coordinator,
                    category="sensors",
                    key=str(key),
                    data=value,
                )
            )

    # =========================================================================
    # FC04 STATUS
    # =========================================================================

    modbus_status = modbus_data.get(
        "status",
        {}
    )

    if isinstance(modbus_status, dict):

        for key, value in modbus_status.items():

            if not isinstance(value, dict):
                continue

            entities.append(
                IDMModbusSensor(
                    coordinator=coordinator,
                    category="status",
                    key=str(key),
                    data=value,
                )
            )

    # =========================================================================
    # FC03 PARAMETER
    # =========================================================================

    modbus_parameters = modbus_data.get(
        "parameters",
        {}
    )

    if isinstance(modbus_parameters, dict):

        for key, value in modbus_parameters.items():

            if not isinstance(value, dict):
                continue

            entities.append(
                IDMModbusSensor(
                    coordinator=coordinator,
                    category="parameters",
                    key=str(key),
                    data=value,
                )
            )

    # =========================================================================
    # REGISTRIEREN
    # =========================================================================

    _LOGGER.debug(
        "iDM MODBUS SENSOR: Registriere %d Entities",
        len(entities),
    )

    async_add_entities(
        entities,
        update_before_add=True,
    )