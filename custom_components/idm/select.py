from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import IDMCoordinator

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# iDM Navigator Select Parameter
# ============================================================================

SYSTEM_MODES = {
    0: "Aus",
    1: "Automatik",
    2: "Warmwasser",
    3: "Warmwasser einmal",
}

SYSTEM_MODE_VALUES = {
    "Aus": 0,
    "Automatik": 1,
    "Warmwasser": 2,
    "Warmwasser einmal": 3,
}


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


# ============================================================================
# Gemeinsamer Lock für Select-Schreibvorgänge
# ============================================================================

_NAV1_WRITE_LOCK = asyncio.Lock()


# ============================================================================
# Gemeinsame Hilfsfunktionen
# ============================================================================


def _find_nav1_field(value: Any, key: str, depth: int = 0) -> Any | None:
    """Sucht rekursiv ein Feld im Navigator-Dashboard."""
    if depth > 20:
        return None

    if isinstance(value, dict):
        if value.get("key") == key and "value" in value:
            return value.get("value")

        for child in value.values():
            result = _find_nav1_field(child, key, depth + 1)
            if result is not None:
                return result

        return None

    if isinstance(value, list):
        for child in value:
            result = _find_nav1_field(child, key, depth + 1)
            if result is not None:
                return result

    return None


async def _read_active_navigator_field(
    coordinator: IDMCoordinator,
    field: str,
) -> Any | None:
    """
    Liest das Navigator-Dashboard direkt über die API.

    Wichtig:
    coordinator.get_navigator_field() liefert nur den gecachten Wert.
    Für die Write-Bestätigung benötigen wir deshalb einen frischen API-Read.
    """
    try:
        dashboard = await coordinator.api.navigator_dashboard()
    except Exception as err:
        _LOGGER.warning(
            "iDM NAV1 READBACK: Frischer Navigator-Read fehlgeschlagen "
            "für Feld '%s': %s",
            field,
            err,
        )
        return None

    if not isinstance(dashboard, dict):
        _LOGGER.warning(
            "iDM NAV1 READBACK: Ungültige Dashboard-Antwort für Feld '%s': %r",
            field,
            dashboard,
        )
        return None

    return _find_nav1_field(dashboard, field)


async def _wait_for_nav1_readback(
    coordinator: IDMCoordinator,
    *,
    address: int,
    field: str,
    commanded_value: int,
    label: str,
    max_attempts: int = 10,
    delay_seconds: float = 1.0,
) -> tuple[bool, Any | None]:
    """
    Wartet nach NC_SET_PARAM auf die Übernahme des Wertes in NAV1.

    Jeder einzelne frische Navigator-Read hat ein eigenes 5-Sekunden-Timeout.

    Rückgabe:
        (True, tatsächlicher Wert)  -> bestätigt
        (False, letzter Wert)       -> Timeout / nicht bestätigt
    """

    _LOGGER.warning(
        "iDM NAV1 READBACK: Starte Polling nach Write %s=%s (%s)",
        address,
        commanded_value,
        label,
    )

    last_value: Any | None = None

    for attempt in range(1, max_attempts + 1):
        await asyncio.sleep(delay_seconds)

        _LOGGER.warning(
            "iDM NAV1 READBACK: Polling %s/%s - "
            "lese NAV1 nach Write %s=%s (%s)",
            attempt,
            max_attempts,
            address,
            commanded_value,
            label,
        )

        # ------------------------------------------------------------------
        # WICHTIG:
        # Ein hängender navigator_dashboard()-Aufruf darf den gesamten
        # Readback-Poller nicht blockieren.
        # ------------------------------------------------------------------
        try:
            value = await asyncio.wait_for(
                _read_active_navigator_field(
                    coordinator,
                    field,
                ),
                timeout=5.0,
            )

        except asyncio.TimeoutError:
            _LOGGER.warning(
                "iDM NAV1 READBACK: TIMEOUT beim frischen "
                "Navigator-Read nach 5 Sekunden - "
                "Polling %s/%s wird fortgesetzt.",
                attempt,
                max_attempts,
            )
            continue

        except Exception as err:
            _LOGGER.warning(
                "iDM NAV1 READBACK: Unerwarteter Fehler beim "
                "Navigator-Read Polling %s/%s: %s",
                attempt,
                max_attempts,
                err,
            )
            continue

        last_value = value

        _LOGGER.warning(
            "iDM NAV1 READBACK: Polling %s/%s | "
            "WRITE %s=%s | NAV1 %s=%s",
            attempt,
            max_attempts,
            address,
            commanded_value,
            field,
            value,
        )

        try:
            actual_value = float(value)
        except (TypeError, ValueError):
            _LOGGER.warning(
                "iDM NAV1 READBACK: Feld '%s' liefert keinen "
                "numerischen Wert: %r",
                field,
                value,
            )
            continue

        difference = abs(actual_value - float(commanded_value))

        if difference < 0.001:
            _LOGGER.warning(
                "iDM NAV1 READBACK: BESTÄTIGT nach %s "
                "Polling-Versuch(en) - "
                "Adresse=%s, geschrieben=%s, NAV1 %s=%s",
                attempt,
                address,
                commanded_value,
                field,
                actual_value,
            )
            return True, actual_value

        _LOGGER.warning(
            "iDM NAV1 READBACK: Noch nicht übernommen - "
            "Adresse=%s, geschrieben=%s, NAV1 %s=%s, Differenz=%s",
            address,
            commanded_value,
            field,
            actual_value,
            difference,
        )

    _LOGGER.warning(
        "iDM NAV1 READBACK: TIMEOUT nach maximaler Polling-Dauer - "
        "Adresse=%s, geschrieben=%s, letzter NAV1-Wert=%s",
        address,
        commanded_value,
        last_value,
    )

    return False, last_value


# ============================================================================
# SYSTEMMODUS – Parameter 2000
# ============================================================================


class IDMSystemModeSelect(
    CoordinatorEntity[IDMCoordinator],
    SelectEntity,
):
    """iDM Navigator Systemmodus – Parameter 2000."""

    _attr_has_entity_name = True
    _attr_name = "Systemmodus"
    _attr_icon = "mdi:heat-pump"
    _attr_options = list(SYSTEM_MODE_VALUES.keys())

    def __init__(self, coordinator: IDMCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"idm_{coordinator.api.wp_id}_system_mode"
        )

        self._attr_current_option: str | None = None
        self._commanded_option: str | None = None

        self._update_current_mode()

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("idm", str(self.coordinator.api.wp_id))
            },
            "name": "iDM Wärmepumpe",
            "manufacturer": "iDM",
            "model": "TERRA S",
        }

    @property
    def current_option(self) -> str | None:
        return self._attr_current_option

    def _handle_coordinator_update(self) -> None:
        self._update_current_mode()
        super()._handle_coordinator_update()

    def _update_current_mode(self) -> None:
        if self._commanded_option is not None:
            if self._attr_current_option != self._commanded_option:
                self._attr_current_option = self._commanded_option
            return

        value = self.coordinator.get_navigator_field(
            "system_mode"
        )

        if value is None:
            return

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return

        mode = min(
            SYSTEM_MODES,
            key=lambda candidate: abs(candidate - numeric_value),
        )

        option = SYSTEM_MODES[mode]

        if self._attr_current_option != option:
            self._attr_current_option = option

    async def async_select_option(self, option: str) -> None:
        """Schreibt Parameter 2000 und bestätigt ihn über NAV1."""

        _LOGGER.warning(
            "iDM SYSTEM SELECT: async_select_option() aufgerufen: %s",
            option,
        )

        if option not in SYSTEM_MODE_VALUES:
            raise ValueError(
                f"Unbekannter iDM Systemmodus: {option}"
            )

        value = SYSTEM_MODE_VALUES[option]

        _LOGGER.warning(
            "iDM SYSTEM SELECT: Setze Systemmodus auf '%s' (%s) "
            "[NC_SET_PARAM 2000]",
            option,
            value,
        )

        async with _NAV1_WRITE_LOCK:
            try:
                result = await self.coordinator.api.set_system_mode(
                    value
                )
            except Exception as err:
                _LOGGER.error(
                    "iDM SYSTEM SELECT: API-Fehler bei "
                    "NC_SET_PARAM 2000=%s: %s",
                    value,
                    err,
                )
                raise

            _LOGGER.warning(
                "iDM SYSTEM SELECT: API erfolgreich aufgerufen: %s",
                result,
            )

            if (
                isinstance(result, dict)
                and result.get("status") != "ok"
            ):
                _LOGGER.error(
                    "iDM SYSTEM SELECT: NC_SET_PARAM 2000=%s "
                    "wurde von der API nicht bestätigt: %s",
                    value,
                    result,
                )
                return

            confirmed, actual_value = (
                await _wait_for_nav1_readback(
                    self.coordinator,
                    address=2000,
                    field="system_mode",
                    commanded_value=value,
                    label=f"Systemmodus '{option}'",
                )
            )

            if confirmed:
                self._attr_current_option = option

                # ----------------------------------------------------------
                # WICHTIG:
                # Der Command ist nach erfolgreichem Readback nicht mehr
                # erforderlich. Künftige Coordinator-Updates sollen wieder
                # ausschließlich den tatsächlichen NAV1-Wert verwenden.
                # ----------------------------------------------------------
                self._commanded_option = None

                _LOGGER.warning(
                    "iDM SYSTEM SELECT: Systemmodus '%s' (%s) "
                    "durch NAV1-Readback bestätigt.",
                    option,
                    value,
                )

                self.async_write_ha_state()
                return

            self._commanded_option = None

            _LOGGER.warning(
                "iDM SYSTEM SELECT: Systemmodus '%s' (%s) "
                "NICHT durch NAV1 bestätigt. "
                "Letzter NAV1-Wert=%s.",
                option,
                value,
                actual_value,
            )

            self._update_current_mode()
            self.async_write_ha_state()


# ============================================================================
# HEIZKREIS A MODUS – Parameter 2002
# ============================================================================


class IDMHeatCircuitModeSelect(
    CoordinatorEntity[IDMCoordinator],
    SelectEntity,
):
    """iDM Navigator Heizkreis-A-Modus – Parameter 2002."""

    _attr_has_entity_name = True
    _attr_name = "Heizkreis A Modus"
    _attr_icon = "mdi:home-thermometer"
    _attr_options = list(MODE_VALUES.keys())

    def __init__(self, coordinator: IDMCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"idm_{coordinator.api.wp_id}_heat_a_mode"
        )

        self._attr_current_option: str | None = None
        self._commanded_option: str | None = None

        self._update_current_mode()

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("idm", str(self.coordinator.api.wp_id))
            },
            "name": "iDM Wärmepumpe",
            "manufacturer": "iDM",
            "model": "TERRA S",
        }

    @property
    def current_option(self) -> str | None:
        return self._attr_current_option

    def _handle_coordinator_update(self) -> None:
        self._update_current_mode()
        super()._handle_coordinator_update()

    def _update_current_mode(self) -> None:
        if self._commanded_option is not None:
            if self._attr_current_option != self._commanded_option:
                self._attr_current_option = self._commanded_option
            return

        value = self.coordinator.get_navigator_field(
            "circuit_mode"
        )

        if value is not None:
            try:
                numeric_value = float(value)

                mode = min(
                    MODES,
                    key=lambda candidate: abs(
                        candidate - numeric_value
                    ),
                )

                option = MODES[mode]

                if self._attr_current_option != option:
                    self._attr_current_option = option

                return

            except (TypeError, ValueError):
                pass

        # Priority 3:
        # Fallback auf Graph-Kanal 130
        try:
            heat_a_graph = self.coordinator.data.get(
                "heat_a_graph"
            )

            if not isinstance(heat_a_graph, dict):
                return

            graph_data = heat_a_graph.get("data")

            if not isinstance(graph_data, list):
                return

            for item in reversed(graph_data):
                if not isinstance(item, dict):
                    continue

                key = item.get("key")

                if str(key) != "130":
                    continue

                graph_value = item.get("value")

                try:
                    numeric_value = float(graph_value)
                except (TypeError, ValueError):
                    continue

                mode = min(
                    MODES,
                    key=lambda candidate: abs(
                        candidate - numeric_value
                    ),
                )

                option = MODES[mode]

                if self._attr_current_option != option:
                    self._attr_current_option = option

                return

        except Exception as err:
            _LOGGER.debug(
                "iDM SELECT: Fehler beim Graph-Fallback "
                "für Heizkreis A: %s",
                err,
            )

    async def async_select_option(self, option: str) -> None:
        """Schreibt Parameter 2002 und bestätigt ihn über NAV1."""

        _LOGGER.warning(
            "iDM SELECT: async_select_option() aufgerufen: %s",
            option,
        )

        if option not in MODE_VALUES:
            raise ValueError(
                f"Unbekannter iDM Heizkreis-A-Modus: {option}"
            )

        value = MODE_VALUES[option]

        _LOGGER.warning(
            "iDM SELECT: Setze Heizkreis A auf '%s' (%s) "
            "[NC_SET_PARAM 2002]",
            option,
            value,
        )

        async with _NAV1_WRITE_LOCK:
            try:
                result = await self.coordinator.api.set_heat_a_mode(
                    value
                )
            except Exception as err:
                _LOGGER.error(
                    "iDM SELECT: API-Fehler bei "
                    "NC_SET_PARAM 2002=%s: %s",
                    value,
                    err,
                )
                raise

            _LOGGER.warning(
                "iDM SELECT: API erfolgreich aufgerufen: %s",
                result,
            )

            if (
                isinstance(result, dict)
                and result.get("status") != "ok"
            ):
                _LOGGER.error(
                    "iDM SELECT: NC_SET_PARAM 2002=%s "
                    "wurde von der API nicht bestätigt: %s",
                    value,
                    result,
                )
                return

            confirmed, actual_value = (
                await _wait_for_nav1_readback(
                    self.coordinator,
                    address=2002,
                    field="circuit_mode",
                    commanded_value=value,
                    label=f"Heizkreis A Modus '{option}'",
                )
            )

            if confirmed:
                self._attr_current_option = option

                # ----------------------------------------------------------
                # WICHTIG:
                # Der Command ist nach erfolgreichem Readback nicht mehr
                # erforderlich. Künftige Coordinator-Updates sollen wieder
                # ausschließlich den tatsächlichen NAV1-Wert verwenden.
                # ----------------------------------------------------------
                self._commanded_option = None

                _LOGGER.warning(
                    "iDM SELECT: Heizkreis-A-Modus '%s' (%s) "
                    "durch NAV1-Readback bestätigt.",
                    option,
                    value,
                )

                self.async_write_ha_state()
                return

            self._commanded_option = None

            _LOGGER.warning(
                "iDM SELECT: Heizkreis-A-Modus '%s' (%s) "
                "NICHT durch NAV1 bestätigt. "
                "Letzter NAV1-Wert=%s.",
                option,
                value,
                actual_value,
            )

            self._update_current_mode()
            self.async_write_ha_state()


# ============================================================================
# Home Assistant Setup
# ============================================================================


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Setzt die iDM Select-Entities auf."""

    coordinator: IDMCoordinator = entry.runtime_data

    async_add_entities(
        [
            IDMSystemModeSelect(coordinator),
            IDMHeatCircuitModeSelect(coordinator),
        ]
    )