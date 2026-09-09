from __future__ import annotations

import logging
import struct
from typing import Any

from pymodbus.client import AsyncModbusTcpClient


_LOGGER = logging.getLogger(__name__)


# ============================================================================
# iDM MODBUS
# ============================================================================
#
# iDM Terra / Navigator
#
# Modbus TCP
# Host     : wird über Config übergeben
# Port     : 502
# Device ID: 1
#
# BESTÄTIGT:
#   FC04 = Read Input Registers
#   FC03 = Read Holding Registers
#
# FLOAT32:
#   Register 1 = LOW WORD
#   Register 2 = HIGH WORD
#
# Beispiel:
#   Adresse 1000
#   LOW  = 0xF5BC
#   HIGH = 0x41A3
#   RAW32 = 0x41A3F5BC
#   FLOAT = 20.494987
#
# WICHTIG:
#   Diese Datei führt KEINE Schreiboperationen aus.
#
# HEIZKREISE:
#   Es wird ausschließlich Heizkreis A verwendet.
#   Heizkreis B-G wurden bewusst entfernt.
#
# ============================================================================


# ============================================================================
# MODBUS REGISTER
# ============================================================================

# ----------------------------------------------------------------------------
# FC04 – INPUT REGISTERS
# ----------------------------------------------------------------------------
#
# Allgemeine iDM Sensorwerte
# sowie ausschließlich Heizkreis A.
# ----------------------------------------------------------------------------

FC04_FLOAT_REGISTERS: dict[int, tuple[str, str | None]] = {
    # ------------------------------------------------------------------------
    # ALLGEMEINE WÄRMEPUMPENWERTE
    # ------------------------------------------------------------------------

    1000: ("Außentemperatur", "°C"),
    1002: ("Wärmepumpe Vorlauf", "°C"),
    1004: ("HGL Vorlauf", "°C"),
    1006: ("Wärmequellenaustrittstemperatur", "°C"),
    1008: ("Wärmepumpe Rücklauf / Wärmespeicher", "°C"),
    1010: ("Kältespeichertemperatur", "°C"),
    1012: ("Trinkwassererwärmertemperatur", "°C"),
    1014: ("Frischwasserzapftemperatur", "°C"),

    # ------------------------------------------------------------------------
    # HEIZKREIS A
    # ------------------------------------------------------------------------

    1016: ("Heizkreis A Vorlauf", "°C"),
    1030: ("Heizkreis A Raumgerät", "°C"),

    # ------------------------------------------------------------------------
    # WEITERE TEMPERATUREN
    # ------------------------------------------------------------------------

    1044: ("Heissgastemperatur", "°C"),
    1046: ("Feuchtesensor", "%"),
    1048: ("Luftansaugtemperatur", "°C"),
    1050: ("Luftwärmetauschertemperatur", "°C"),
    1052: ("Solar Kollektortemperatur", "°C"),
    1054: ("Solar Ladetemperatur", "°C"),
    1056: ("Solar Kollektorrücklauftemperatur", "°C"),
    1058: (
        "Solar Wärmequellenreferenz / Pooltemperatur",
        "°C",
    ),
    1060: ("Gemittelte Außentemperatur", "°C"),
    1062: ("Wärmequelleneintrittstemperatur", "°C"),
    1064: (
        "iDM Systemkühlung Ladefühler Kühlen",
        "°C",
    ),
    1066: (
        "iDM Systemkühlung Rückkühlfühler",
        "°C",
    ),

    # ------------------------------------------------------------------------
    # WÄRMEMENGEN / LEISTUNG
    # ------------------------------------------------------------------------

    1068: ("Wärmemenge Wärmepumpenvorlauf", "kW"),
    1070: ("Wärmemenge HGL-Vorlauf", "kW"),
    1072: ("Wärmemenge Momentanleistung", "kW"),
    1074: ("Wärmemenge Solar", "kW"),
    1076: ("Wärmemenge gesamt", "kWh"),
    1078: ("Wärmemenge Heizen gesamt", "kWh"),
    1080: ("Wärmemenge HGL gesamt", "kWh"),
    1082: ("Wärmemenge Kühlen gesamt", "kWh"),
    1084: ("Wärmemenge Warmwasser gesamt", "kWh"),
    1086: ("Wärmemenge Solar gesamt", "kWh"),
    1088: ("Wärmemenge Quelle gesamt", "kWh"),
}


# ----------------------------------------------------------------------------
# FC04 – STATUS / UCHAR
# ----------------------------------------------------------------------------
#
# Nur Heizkreis A.
# ----------------------------------------------------------------------------

FC04_STATUS_REGISTERS: dict[int, str] = {
    1500: "Status System",
    1501: "Status Heizkreis A",

    1508: "Status Verdichter 1",
    1509: "Status Verdichter 2",
    1510: "Status Verdichter 3",
    1511: "Status Verdichter 4",

    1512: "Status Ladepumpe",
    1513: "Status Wärmequellenpumpe",
    1514: "Status Zwischenkreispumpe",
    1515: "Status ISC Kältespeicherpumpe",
    1516: "Status ISC Rückkühlpumpe",

    1517: (
        "Anzahl laufende Verdichterstufen "
        "Heizen gesamt"
    ),
    1518: (
        "Anzahl laufende Verdichterstufen "
        "Kühlen gesamt"
    ),
    1519: (
        "Anzahl laufende Verdichterstufen "
        "Vorrang gesamt"
    ),

    1520: "Betriebsart Kaskade",
    1521: "Betriebsart Solar",
    1522: "Smart Grid Status",
    1523: "iDM Systemkühlung ISC Modus",
    1524: "Reserviert / Dokumentationsprüfung",
}


# ----------------------------------------------------------------------------
# FC03 – HOLDING REGISTERS
# ----------------------------------------------------------------------------
#
# Nur Heizkreis A.
# ----------------------------------------------------------------------------

FC03_REGISTERS: dict[int, tuple[str, str, str | None]] = {
    # ------------------------------------------------------------------------
    # SYSTEM
    # ------------------------------------------------------------------------

    2000: (
        "Betriebsart System",
        "uchar",
        None,
    ),

    # ------------------------------------------------------------------------
    # HEIZKREIS A – BETRIEBSART
    # ------------------------------------------------------------------------

    2002: (
        "Betriebsart Heizkreis A",
        "uchar",
        None,
    ),

    # ------------------------------------------------------------------------
    # HEIZKREIS A – HEIZEN
    # ------------------------------------------------------------------------

    2016: (
        "Raumsolltemperatur Heizen Normal Heizkreis A",
        "float32",
        "°C",
    ),

    2030: (
        "Raumsolltemperatur Heizen ECO Heizkreis A",
        "float32",
        "°C",
    ),

    2044: (
        "Heizkurve Heizkreis A",
        "float32",
        None,
    ),

    2058: (
        "Heizgrenze Heizkreis A",
        "uchar",
        "°C",
    ),

    2072: (
        "Sollvorlauftemperatur Heizen Heizkreis A",
        "uchar",
        "°C",
    ),

    # ------------------------------------------------------------------------
    # HEIZKREIS A – KÜHLEN
    # ------------------------------------------------------------------------

    2086: (
        "Raumsolltemperatur Kühlen Normal Heizkreis A",
        "float32",
        "°C",
    ),

    2100: (
        "Raumsolltemperatur Kühlen ECO Heizkreis A",
        "float32",
        "°C",
    ),

    2114: (
        "Kühlgrenze Heizkreis A",
        "uchar",
        "°C",
    ),

    2128: (
        "Sollvorlauftemperatur Kühlen Heizkreis A",
        "uchar",
        "°C",
    ),

    # ------------------------------------------------------------------------
    # EXTERNE / SYSTEMWERTE
    # ------------------------------------------------------------------------

    2142: (
        "Externe Anforderungstemperatur Heizen",
        "uchar",
        "°C",
    ),

    2144: (
        "Externe Anforderungstemperatur Kühlen",
        "uchar",
        "°C",
    ),

    2146: (
        "Bivalenzpunkt 1",
        "word",
        "°C",
    ),

    2148: (
        "Bivalenzpunkt 2",
        "word",
        "°C",
    ),

    2150: (
        "Betriebsart Solar",
        "uchar",
        None,
    ),

    2152: (
        "Frischwasser-Solltemperatur",
        "float32",
        "°C",
    ),
}


# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================


def decode_float32(registers: list[int]) -> float:
    """Dekodiert einen iDM FLOAT32-Wert.

    iDM liefert:

        registers[0] = LOW WORD
        registers[1] = HIGH WORD

    Das resultierende Byte-/Word-Layout wird deshalb entsprechend
    zusammengesetzt.
    """

    if len(registers) < 2:
        raise ValueError(
            "FLOAT32 benötigt zwei Register."
        )

    low_word = int(registers[0]) & 0xFFFF
    high_word = int(registers[1]) & 0xFFFF

    raw32 = (
        (high_word << 16)
        | low_word
    )

    return struct.unpack(
        ">f",
        raw32.to_bytes(
            4,
            byteorder="big",
        ),
    )[0]


def decode_word(registers: list[int]) -> int:
    """Dekodiert ein vorzeichenbehaftetes 16-Bit WORD."""

    if not registers:
        raise ValueError(
            "WORD benötigt ein Register."
        )

    value = int(registers[0]) & 0xFFFF

    if value & 0x8000:
        value -= 0x10000

    return value


def decode_uchar(registers: list[int]) -> int:
    """Dekodiert einen UCHAR-Wert aus einem Modbus-Register."""

    if not registers:
        raise ValueError(
            "UCHAR benötigt ein Register."
        )

    return int(registers[0]) & 0xFF


# ============================================================================
# MODBUS CLIENT
# ============================================================================


class IDMModbus:
    """READ-ONLY Modbus TCP Zugriff auf eine iDM Wärmepumpe."""

    def __init__(
        self,
        host: str,
        port: int = 502,
        device_id: int = 1,
        timeout: float = 2.0,
    ) -> None:
        """Initialisiert den Modbus-Zugriff."""

        self.host = host
        self.port = port
        self.device_id = device_id
        self.timeout = timeout

        self.client = AsyncModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
        )

    # =========================================================================
    # CONNECT
    # =========================================================================

    async def async_connect(self) -> bool:
        """Verbindet sich mit der iDM Wärmepumpe."""

        try:
            await self.client.connect()

        except Exception:
            _LOGGER.exception(
                "iDM MODBUS: Verbindung fehlgeschlagen"
            )
            return False

        if not self.client.connected:
            _LOGGER.error(
                "iDM MODBUS: "
                "Verbindung konnte nicht hergestellt werden"
            )
            return False

        _LOGGER.debug(
            "iDM MODBUS: verbunden mit %s:%s device_id=%s",
            self.host,
            self.port,
            self.device_id,
        )

        return True

    # =========================================================================
    # DISCONNECT
    # =========================================================================

    async def async_close(self) -> None:
        """Schließt die Modbus-Verbindung."""

        try:
            self.client.close()

        except Exception:
            _LOGGER.exception(
                "iDM MODBUS: Fehler beim Schließen"
            )

    # =========================================================================
    # FC04
    # =========================================================================

    async def read_input_registers(
        self,
        address: int,
        count: int,
    ) -> list[int]:
        """Liest Input Register über FC04."""

        try:
            response = await self.client.read_input_registers(
                address=address,
                count=count,
                device_id=self.device_id,
            )

        except Exception as err:
            _LOGGER.error(
                "iDM MODBUS FC04 Fehler: "
                "address=%s count=%s error=%s",
                address,
                count,
                err,
            )
            raise

        if response.isError():
            raise RuntimeError(
                f"FC04 Fehler bei Adresse {address}: "
                f"{response}"
            )

        registers = list(
            response.registers
        )

        _LOGGER.debug(
            "iDM MODBUS FC04: "
            "address=%s count=%s registers=%s",
            address,
            count,
            registers,
        )

        return registers

    # =========================================================================
    # FC03
    # =========================================================================

    async def read_holding_registers(
        self,
        address: int,
        count: int,
    ) -> list[int]:
        """Liest Holding Register über FC03."""

        try:
            response = await self.client.read_holding_registers(
                address=address,
                count=count,
                device_id=self.device_id,
            )

        except Exception as err:
            _LOGGER.error(
                "iDM MODBUS FC03 Fehler: "
                "address=%s count=%s error=%s",
                address,
                count,
                err,
            )
            raise

        if response.isError():
            raise RuntimeError(
                f"FC03 Fehler bei Adresse {address}: "
                f"{response}"
            )

        registers = list(
            response.registers
        )

        _LOGGER.debug(
            "iDM MODBUS FC03: "
            "address=%s count=%s registers=%s",
            address,
            count,
            registers,
        )

        return registers

    # =========================================================================
    # EINZELNER FLOAT32 FC04
    # =========================================================================

    async def read_float32(
        self,
        address: int,
    ) -> float:
        """Liest einen FLOAT32-Wert über FC04."""

        registers = await self.read_input_registers(
            address=address,
            count=2,
        )

        return decode_float32(
            registers
        )

    # =========================================================================
    # EINZELNER UCHAR FC04
    # =========================================================================

    async def read_status(
        self,
        address: int,
    ) -> int:
        """Liest einen Status/UCHAR über FC04."""

        registers = await self.read_input_registers(
            address=address,
            count=1,
        )

        return decode_uchar(
            registers
        )

    # =========================================================================
    # EINZELNER UCHAR FC03
    # =========================================================================

    async def read_uchar(
        self,
        address: int,
    ) -> int:
        """Liest einen UCHAR über FC03."""

        registers = await self.read_holding_registers(
            address=address,
            count=1,
        )

        return decode_uchar(
            registers
        )

    # =========================================================================
    # EINZELNER FLOAT32 FC03
    # =========================================================================

    async def read_holding_float32(
        self,
        address: int,
    ) -> float:
        """Liest einen FLOAT32-Wert über FC03."""

        registers = await self.read_holding_registers(
            address=address,
            count=2,
        )

        return decode_float32(
            registers
        )

    # =========================================================================
    # EINZELNER WORD FC03
    # =========================================================================

    async def read_word(
        self,
        address: int,
    ) -> int:
        """Liest ein WORD über FC03."""

        registers = await self.read_holding_registers(
            address=address,
            count=1,
        )

        return decode_word(
            registers
        )

    # =========================================================================
    # GESAMTE SENSOR-DATEN
    # =========================================================================

    async def read_all_sensors(
        self,
    ) -> dict[str, Any]:
        """Liest die für Home Assistant relevanten FC04-Daten."""

        result: dict[str, Any] = {}

        for address, (
            name,
            unit,
        ) in FC04_FLOAT_REGISTERS.items():

            try:
                value = await self.read_float32(
                    address
                )

            except Exception as err:
                _LOGGER.debug(
                    "iDM MODBUS: Sensor %s (%s) "
                    "nicht lesbar: %s",
                    address,
                    name,
                    err,
                )
                continue

            key = self._make_key(
                name
            )

            result[key] = {
                "value": round(
                    value,
                    2,
                ),
                "unit": unit,
                "address": address,
                "fc": 4,
                "datatype": "float32",
                "name": name,
            }

        return result

    # =========================================================================
    # FC03 PARAMETER
    # =========================================================================

    async def read_all_parameters(
        self,
    ) -> dict[str, Any]:
        """Liest alle dokumentierten FC03-Parameter."""

        result: dict[str, Any] = {}

        for address, (
            name,
            datatype,
            unit,
        ) in FC03_REGISTERS.items():

            try:

                if datatype == "float32":
                    value = await self.read_holding_float32(
                        address
                    )

                elif datatype == "uchar":
                    value = await self.read_uchar(
                        address
                    )

                elif datatype == "word":
                    value = await self.read_word(
                        address
                    )

                else:
                    _LOGGER.warning(
                        "iDM MODBUS: "
                        "unbekannter Datentyp %s "
                        "bei Adresse %s",
                        datatype,
                        address,
                    )
                    continue

            except Exception as err:

                _LOGGER.debug(
                    "iDM MODBUS: Parameter %s (%s) "
                    "nicht lesbar: %s",
                    address,
                    name,
                    err,
                )

                continue

            key = self._make_key(
                name
            )

            if isinstance(
                value,
                float,
            ):
                value = round(
                    value,
                    2,
                )

            result[key] = {
                "value": value,
                "unit": unit,
                "address": address,
                "fc": 3,
                "datatype": datatype,
                "name": name,
            }

        return result

    # =========================================================================
    # STATUS
    # =========================================================================

    async def read_all_status(
        self,
    ) -> dict[str, Any]:
        """Liest die dokumentierten FC04-Statusregister."""

        result: dict[str, Any] = {}

        for address, name in FC04_STATUS_REGISTERS.items():

            try:
                value = await self.read_status(
                    address
                )

            except Exception as err:

                _LOGGER.debug(
                    "iDM MODBUS: Status %s (%s) "
                    "nicht lesbar: %s",
                    address,
                    name,
                    err,
                )

                continue

            key = self._make_key(
                name
            )

            result[key] = {
                "value": value,
                "unit": None,
                "address": address,
                "fc": 4,
                "datatype": "uchar",
                "name": name,
            }

        return result

    # =========================================================================
    # KOMPLETTER READ-ONLY DATENSATZ
    # =========================================================================

    async def read_all(
        self,
    ) -> dict[str, Any]:
        """Liest Sensoren, Status und Parameter."""

        sensors = await self.read_all_sensors()
        status = await self.read_all_status()
        parameters = await self.read_all_parameters()

        return {
            "sensors": sensors,
            "status": status,
            "parameters": parameters,
        }

    # =========================================================================
    # KEY
    # =========================================================================

    @staticmethod
    def _make_key(
        name: str,
    ) -> str:
        """Erzeugt einen einfachen stabilen Entity-Key."""

        replacements = {
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "Ä": "Ae",
            "Ö": "Oe",
            "Ü": "Ue",
            "ß": "ss",
            "/": "_",
            "-": "_",
            " ": "_",
        }

        result = name

        for old, new in replacements.items():
            result = result.replace(
                old,
                new,
            )

        while "__" in result:
            result = result.replace(
                "__",
                "_",
            )

        return result.lower().strip("_")