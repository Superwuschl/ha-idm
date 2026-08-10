from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# ============================================================
# SYSTEM-SENSOREN
# ============================================================

SYSTEM_SENSORS = {
    "1": (
        "aussentemperatur",
        "Außentemperatur",
        SensorDeviceClass.TEMPERATURE,
        "°C",
    ),
    "2": (
        "warmepumpe_vorlauf",
        "Wärmepumpe Vorlauf",
        SensorDeviceClass.TEMPERATURE,
        "°C",
    ),
    "4": (
        "waermequelle",
        "Wärmequelle",
        SensorDeviceClass.TEMPERATURE,
        "°C",
    ),
    "5": (
        "waermepumpe_speicher",
        "Wärmepumpe Speicher",
        SensorDeviceClass.TEMPERATURE,
        "°C",
    ),
    "6": (
        "kaltpuffer",
        "Kaltpuffer",
        SensorDeviceClass.TEMPERATURE,
        "°C",
    ),
    "7": (
        "warmwasser_unten",
        "Warmwasser unten",
        SensorDeviceClass.TEMPERATURE,
        "°C",
    ),
}


# ============================================================
# HEIZKREIS A
# ============================================================

HEAT_A_SENSORS = {
    "9": (
        "heizkreis_a_vorlauf",
        "Heizkreis A Vorlauf",
        SensorDeviceClass.TEMPERATURE,
        "°C",
    ),
    "99": (
        "heizkreis_a_soll_vorlauf",
        "Heizkreis A Soll Vorlauf",
        SensorDeviceClass.TEMPERATURE,
        "°C",
    ),
    "16": (
        "heizkreis_a_raum",
        "Heizkreis A Raum",
        SensorDeviceClass.TEMPERATURE,
        "°C",
    ),
    "106": (
        "heizkreis_a_soll_raum",
        "Heizkreis A Soll Raum",
        SensorDeviceClass.TEMPERATURE,
        "°C",
    ),
    "123": (
        "heizkreis_a_aktiv",
        "Heizkreis A aktiv",
        None,
        None,
    ),
    "130": (
        "heizkreis_a_modus",
        "Heizkreis A Modus",
        None,
        None,
    ),
}


# ============================================================
# HEIZKREIS-A-MODI
# ============================================================

HEAT_A_MODES = {
    0: "Aus",
    1: "Zeitprogramm",
    2: "Normal",
    3: "Eco",
    4: "Manuell Heizen",
    5: "Manuell Kühlen",
}


# ============================================================
# WÄRMEPUMPEN-STAMMDATEN
# ============================================================

HEATPUMP_SENSORS = {
    "online": (
        "warmepumpe_online",
        "Wärmepumpe Online",
        None,
        None,
    ),
    "last_online": (
        "warmepumpe_letzte_verbindung",
        "Wärmepumpe letzte Verbindung",
        SensorDeviceClass.TIMESTAMP,
        None,
    ),
    "logfreq": (
        "idm_logintervall",
        "iDM Logintervall",
        None,
        "s",
    ),
}


# ============================================================
# WÄRMEPUMPEN-INFORMATIONEN
# ============================================================

HEATPUMP_INFO_SENSORS = {
    "wp_type": (
        "warmepumpe_modell",
        "Wärmepumpe Modell",
    ),
    "serialnumber": (
        "warmepumpe_seriennummer",
        "Wärmepumpe Seriennummer",
    ),
    "myidm_id": (
        "warmepumpe_myidm_id",
        "Wärmepumpe myIDM ID",
    ),
    "nav_version": (
        "warmepumpe_navigator_version",
        "Wärmepumpe Navigator Version",
    ),
    "navpro_version": (
        "warmepumpe_navigator_pro_version",
        "Wärmepumpe Navigator Pro Version",
    ),
    "navpro_online": (
        "warmepumpe_navigator_pro_online",
        "Wärmepumpe Navigator Pro Online",
    ),
}


# ============================================================
# GERÄTEINFORMATION
# ============================================================

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

    if serialnumber is not None:
        serial = str(serialnumber)
    elif wp_id is not None:
        serial = str(wp_id)
    else:
        serial = "unknown"

    if name:
        device_name = str(name)
    elif wp_type:
        device_name = f"iDM {wp_type}"
    else:
        device_name = "iDM Wärmepumpe"

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


# ============================================================
# SETUP
# ============================================================

async def async_setup_entry(
    hass: Any,
    entry: Any,
    async_add_entities,
) -> None:
    """Erstellt alle iDM Sensoren."""

    coordinator = entry.runtime_data

    entities = []

    # --------------------------------------------------------
    # SYSTEM
    # --------------------------------------------------------

    for channel, config in SYSTEM_SENSORS.items():
        entities.append(
            IDMValueSensor(
                coordinator=coordinator,
                graph_name="system",
                channel=channel,
                key=config[0],
                name=config[1],
                device_class=config[2],
                unit=config[3],
            )
        )

    # --------------------------------------------------------
    # HEIZKREIS A
    # --------------------------------------------------------

    for channel, config in HEAT_A_SENSORS.items():
        entities.append(
            IDMValueSensor(
                coordinator=coordinator,
                graph_name="heat_a",
                channel=channel,
                key=config[0],
                name=config[1],
                device_class=config[2],
                unit=config[3],
            )
        )

    # --------------------------------------------------------
    # WÄRMEPUMPEN-STAMMDATEN
    # --------------------------------------------------------

    for field, config in HEATPUMP_SENSORS.items():
        entities.append(
            IDMHeatpumpSensor(
                coordinator=coordinator,
                field=field,
                key=config[0],
                name=config[1],
                device_class=config[2],
                unit=config[3],
            )
        )

    # --------------------------------------------------------
    # WÄRMEPUMPEN-INFORMATIONEN
    # --------------------------------------------------------

    for field, config in HEATPUMP_INFO_SENSORS.items():
        entities.append(
            IDMHeatpumpInfoSensor(
                coordinator=coordinator,
                field=field,
                key=config[0],
                name=config[1],
            )
        )

    _LOGGER.debug(
        "iDM SENSOR: Registriere %d Entities",
        len(entities),
    )

    async_add_entities(
        entities,
        update_before_add=True,
    )


# ============================================================
# DIAGRAMM-SENSOR
# ============================================================

class IDMValueSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """Sensor für einen einzelnen Kanal eines iDM-Diagramms."""

    def __init__(
        self,
        coordinator,
        graph_name: str,
        channel: str,
        key: str,
        name: str,
        device_class,
        unit: str | None,
    ) -> None:
        """Initialisiert den Diagramm-Sensor."""

        super().__init__(coordinator)

        self.graph_name = graph_name
        self.channel = str(channel)
        self.key = key

        self._attr_name = name
        self._attr_unique_id = (
            f"{DOMAIN}_{graph_name}_{self.channel}"
        )

        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_has_entity_name = False

    @property
    def device_info(self) -> DeviceInfo:
        """Liefert die gemeinsame iDM Geräteinformation."""

        return _get_device_info(self.coordinator)

    # --------------------------------------------------------
    # DIAGRAMM SUCHEN
    # --------------------------------------------------------

    def _get_graph(self) -> dict[str, Any] | None:
        """Findet das benötigte Diagramm."""

        if not self.coordinator.data:
            return None

        if self.graph_name == "system":
            graph = self.coordinator.data.get(
                "system_graph"
            )

        elif self.graph_name == "heat_a":
            graph = self.coordinator.data.get(
                "heat_a_graph"
            )

        else:
            return None

        if not isinstance(graph, dict):
            return None

        return graph

    # --------------------------------------------------------
    # LETZTEN WERT SUCHEN
    # --------------------------------------------------------

    def _get_last_value(self) -> Any:
        """Liefert den letzten gültigen Wert des Kanals."""

        graph = self._get_graph()

        if graph is None:
            return None

        data = graph.get("data")

        if not isinstance(data, list) or not data:
            return None

        for point in reversed(data):

            if not isinstance(point, dict):
                continue

            if self.channel not in point:
                continue

            value = point.get(self.channel)

            if value is None:
                continue

            return value

        _LOGGER.debug(
            "iDM SENSOR %s: Kanal %s nicht geliefert",
            self.name,
            self.channel,
        )

        return None

    # --------------------------------------------------------
    # SENSORWERT
    # --------------------------------------------------------

    @property
    def native_value(self) -> Any:
        """Liefert den aktuellen Sensorwert."""

        value = self._get_last_value()

        if value is None:
            return None

        # ----------------------------------------------------
        # HEIZKREIS A AKTIV
        # ----------------------------------------------------

        if (
            self.graph_name == "heat_a"
            and self.channel == "123"
        ):
            try:
                return float(value) != 0.0

            except (TypeError, ValueError):
                return None

        # ----------------------------------------------------
        # HEIZKREIS A MODUS
        # ----------------------------------------------------

        if (
            self.graph_name == "heat_a"
            and self.channel == "130"
        ):
            try:
                mode = int(float(value))

            except (TypeError, ValueError):
                return None

            return HEAT_A_MODES.get(
                mode,
                f"Unbekannt ({value})",
            )

        # ----------------------------------------------------
        # NUMERISCH
        # ----------------------------------------------------

        try:
            return round(
                float(value),
                2,
            )

        except (TypeError, ValueError):
            _LOGGER.debug(
                "iDM SENSOR %s: Ungültiger Wert=%r",
                self.name,
                value,
            )

            return None


# ============================================================
# WÄRMEPUMPEN-STAMMDATEN
# ============================================================

class IDMHeatpumpSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """Sensor für einen Wert aus den iDM Stammdaten."""

    def __init__(
        self,
        coordinator,
        field: str,
        key: str,
        name: str,
        device_class,
        unit: str | None,
    ) -> None:
        """Initialisiert den Stammdaten-Sensor."""

        super().__init__(coordinator)

        self.field = field
        self.key = key

        self._attr_name = name

        self._attr_unique_id = (
            f"{DOMAIN}_heatpump_{field}"
        )

        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_has_entity_name = False

    @property
    def device_info(self) -> DeviceInfo:
        """Liefert die gemeinsame iDM Geräteinformation."""

        return _get_device_info(self.coordinator)

    @property
    def native_value(self) -> Any:
        """Liefert den Wert aus den Wärmepumpen-Stammdaten."""

        if not self.coordinator.data:
            return None

        heatpump = self.coordinator.data.get(
            "heatpump"
        )

        if not isinstance(heatpump, dict):
            return None

        value = heatpump.get(self.field)

        if value is None:
            return None

        # ----------------------------------------------------
        # ONLINE
        # ----------------------------------------------------

        if self.field == "online":

            if isinstance(value, bool):
                return value

            if isinstance(value, str):

                value_lower = value.strip().lower()

                if value_lower in (
                    "true",
                    "1",
                    "online",
                    "yes",
                ):
                    return True

                if value_lower in (
                    "false",
                    "0",
                    "offline",
                    "no",
                ):
                    return False

            return None

        # ----------------------------------------------------
        # LETZTE VERBINDUNG
        # ----------------------------------------------------

        if self.field == "last_online":

            if isinstance(value, datetime):

                if value.tzinfo is None:
                    return value.replace(
                        tzinfo=dt_util.UTC
                    )

                return value

            if isinstance(value, (int, float)):

                try:
                    return datetime.fromtimestamp(
                        value,
                        tz=dt_util.UTC,
                    )

                except (
                    ValueError,
                    OSError,
                    OverflowError,
                ):
                    return None

            if isinstance(value, str):

                try:
                    parsed = datetime.fromisoformat(
                        value.replace(
                            "Z",
                            "+00:00",
                        )
                    )

                    if parsed.tzinfo is None:
                        parsed = parsed.replace(
                            tzinfo=dt_util.UTC
                        )

                    return parsed

                except ValueError:
                    return None

            return None

        # ----------------------------------------------------
        # LOGINTERVALL
        # ----------------------------------------------------

        if self.field == "logfreq":

            try:
                return float(value)

            except (
                TypeError,
                ValueError,
            ):
                return None

        return value


# ============================================================
# WÄRMEPUMPEN-INFORMATIONEN
# ============================================================

class IDMHeatpumpInfoSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """Sensor für zusätzliche iDM Informationen."""

    def __init__(
        self,
        coordinator,
        field: str,
        key: str,
        name: str,
    ) -> None:
        """Initialisiert den Informations-Sensor."""

        super().__init__(coordinator)

        self.field = field
        self.key = key

        self._attr_name = name

        self._attr_unique_id = (
            f"{DOMAIN}_heatpump_info_{field}"
        )

        self._attr_has_entity_name = False

    @property
    def device_info(self) -> DeviceInfo:
        """Liefert die gemeinsame iDM Geräteinformation."""

        return _get_device_info(self.coordinator)

    @property
    def native_value(self) -> Any:
        """Liefert die Information aus den Stammdaten."""

        if not self.coordinator.data:
            return None

        heatpump = self.coordinator.data.get(
            "heatpump"
        )

        if not isinstance(heatpump, dict):
            return None

        value = heatpump.get(self.field)

        if value is None:
            return None

        # ----------------------------------------------------
        # NAVIGATOR PRO ONLINE
        # ----------------------------------------------------

        if self.field == "navpro_online":

            if isinstance(value, bool):
                return value

            if isinstance(value, str):

                value_lower = value.strip().lower()

                if value_lower in (
                    "true",
                    "1",
                    "online",
                    "yes",
                ):
                    return True

                if value_lower in (
                    "false",
                    "0",
                    "offline",
                    "no",
                ):
                    return False

            return None

        return str(value)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Liefert zusätzliche Informationen zum Sensor."""

        heatpump: dict[str, Any] = {}

        if self.coordinator.data:
            heatpump = self.coordinator.data.get(
                "heatpump",
                {},
            )

        if not isinstance(heatpump, dict):
            heatpump = {}

        wp_id = heatpump.get("wp_id")

        return {
            "iDM Feld": self.field,
            "Wärmepumpe ID": (
                str(wp_id)
                if wp_id is not None
                else None
            ),
        }