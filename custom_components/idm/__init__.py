from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import IDMCoordinator
from .modbus import IDMModbus


_LOGGER = logging.getLogger(__name__)


# ============================================================================
# iDM INTEGRATION
# ============================================================================


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    """Richtet die iDM Integration ein."""

    hass.data.setdefault(
        DOMAIN,
        {},
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Richtet eine iDM Config Entry ein."""

    _LOGGER.debug(
        "iDM: Setup gestartet"
    )

    # ========================================================================
    # CONFIG
    # ========================================================================

    config = entry.data

    _LOGGER.warning(
        "iDM DIAGNOSE: Config-Entry Keys=%s",
        sorted(config.keys()),
    )

    _LOGGER.warning(
        "iDM DIAGNOSE: Options Keys=%s",
        sorted(entry.options.keys()),
    )

    # ========================================================================
    # WP-ID
    # ========================================================================

    wp_id = config.get(
        "wp_id"
    )

    if wp_id is None:
        wp_id = config.get(
            "heatpump_id"
        )

    if wp_id is None:
        wp_id = config.get(
            "id"
        )

    if wp_id is None:
        wp_id = entry.options.get(
            "wp_id"
        )

    if wp_id is None:
        wp_id = entry.options.get(
            "heatpump_id"
        )

    if wp_id is None:
        wp_id = entry.options.get(
            "id"
        )

    if wp_id is None:
        wp_id = 3419

    try:
        wp_id = int(
            wp_id
        )

    except (
        TypeError,
        ValueError,
    ):
        _LOGGER.warning(
            "iDM: Ungültige WP-ID - "
            "verwende 3419"
        )

        wp_id = 3419

    _LOGGER.warning(
        "iDM DIAGNOSE: WP-ID=%s",
        wp_id,
    )

    # ========================================================================
    # MODBUS KONFIGURATION
    # ========================================================================

    modbus_host = config.get(
        "modbus_host",
        entry.options.get(
            "modbus_host",
            "192.168.30.188",
        ),
    )

    modbus_port = int(
        config.get(
            "modbus_port",
            entry.options.get(
                "modbus_port",
                502,
            ),
        )
    )

    modbus_device_id = int(
        config.get(
            "modbus_device_id",
            entry.options.get(
                "modbus_device_id",
                1,
            ),
        )
    )

    modbus_timeout = float(
        config.get(
            "modbus_timeout",
            entry.options.get(
                "modbus_timeout",
                2.0,
            ),
        )
    )

    _LOGGER.debug(
        "iDM: Modbus Konfiguration "
        "host=%s port=%s device_id=%s timeout=%s",
        modbus_host,
        modbus_port,
        modbus_device_id,
        modbus_timeout,
    )

    # ========================================================================
    # MODBUS
    # ========================================================================

    modbus = IDMModbus(
        host=modbus_host,
        port=modbus_port,
        device_id=modbus_device_id,
        timeout=modbus_timeout,
    )

    # ========================================================================
    # MYIDM API
    # ========================================================================
    #
    # Wir prüfen sowohl entry.data als auch entry.options.
    #
    # Der Token selbst wird NIEMALS geloggt.
    #
    # ========================================================================

    api = None

    access_token = config.get(
        "access_token"
    )

    token_source = "entry.data"

    if not access_token:

        access_token = entry.options.get(
            "access_token"
        )

        token_source = "entry.options"

    # ------------------------------------------------------------------------
    # TOKEN DIAGNOSE
    # ------------------------------------------------------------------------

    if access_token:

        _LOGGER.warning(
            "iDM DIAGNOSE: Access Token vorhanden "
            "(Quelle=%s, Länge=%d)",
            token_source,
            len(access_token),
        )

    else:

        _LOGGER.error(
            "iDM DIAGNOSE: KEIN Access Token gefunden. "
            "Geprüft wurden entry.data['access_token'] "
            "und entry.options['access_token']."
        )

    # ------------------------------------------------------------------------
    # API INITIALISIEREN
    # ------------------------------------------------------------------------

    if access_token:

        try:

            from .api import IDMApi

            _LOGGER.warning(
                "iDM DIAGNOSE: Initialisiere IDMApi "
                "mit WP-ID=%s",
                wp_id,
            )

            api = IDMApi(
                hass=hass,
                wp_id=wp_id,
                access_token=access_token,
                refresh_token=config.get(
                    "refresh_token"
                )
                or entry.options.get(
                    "refresh_token"
                ),
            )

            _LOGGER.warning(
                "iDM DIAGNOSE: IDMApi erfolgreich "
                "initialisiert"
            )

        except Exception as err:

            _LOGGER.error(
                "iDM DIAGNOSE: IDMApi-Initialisierung "
                "FEHLGESCHLAGEN: %s",
                err,
                exc_info=True,
            )

            api = None

    # ========================================================================
    # API STATUS
    # ========================================================================

    if api is None:

        _LOGGER.error(
            "iDM DIAGNOSE: coordinator.api = None"
        )

        _LOGGER.error(
            "iDM DIAGNOSE: NAV1 select/number können "
            "so nicht funktionieren."
        )

    else:

        _LOGGER.warning(
            "iDM DIAGNOSE: coordinator.api wird "
            "mit gültiger IDMApi-Instanz erstellt"
        )

    # ========================================================================
    # COORDINATOR
    # ========================================================================

    coordinator = IDMCoordinator(
        hass=hass,
        api=api,
        modbus=modbus,
    )

    # ========================================================================
    # ERSTES UPDATE
    # ========================================================================

    await coordinator.async_config_entry_first_refresh()

    # ========================================================================
    # RUNTIME DATA
    # ========================================================================

    entry.runtime_data = coordinator

    hass.data.setdefault(
        DOMAIN,
        {},
    )

    hass.data[DOMAIN][
        entry.entry_id
    ] = coordinator

    # ========================================================================
    # PLATFORMS
    # ========================================================================

    await hass.config_entries.async_forward_entry_setups(
        entry,
        [
            "sensor",
            "select",
            "number",
        ],
    )

    # ========================================================================
    # ABSCHLUSS
    # ========================================================================

    _LOGGER.debug(
        "iDM: Setup erfolgreich"
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Entlädt eine iDM Config Entry."""

    _LOGGER.debug(
        "iDM: Unload gestartet"
    )

    unload_ok = (
        await hass.config_entries.async_unload_platforms(
            entry,
            [
                "sensor",
                "select",
                "number",
            ],
        )
    )

    coordinator = hass.data.get(
        DOMAIN,
        {},
    ).pop(
        entry.entry_id,
        None,
    )

    if coordinator is not None:

        try:

            await coordinator.async_shutdown()

        except Exception:

            _LOGGER.exception(
                "iDM: Fehler beim Shutdown"
            )

    return unload_ok