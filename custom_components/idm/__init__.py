from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import IDMApi
from .const import DOMAIN
from .coordinator import IDMCoordinator


_LOGGER = logging.getLogger(__name__)


PLATFORMS = [
    "sensor",
    "select",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Richtet die iDM Integration ein."""

    # ============================================================
    # API
    # ============================================================

    api = IDMApi(
        hass=hass,
        access_token=entry.data["access_token"],
        wp_id=entry.data["wp_id"],
    )

    # ============================================================
    # COORDINATOR
    # ============================================================

    coordinator = IDMCoordinator(
        hass=hass,
        api=api,
    )

    # ============================================================
    # ERSTER DATENABRUF
    # ============================================================

    await coordinator.async_config_entry_first_refresh()

    # ============================================================
    # RUNTIME DATA
    # ============================================================

    entry.runtime_data = coordinator

    # ============================================================
    # PLATTFORMEN
    # ============================================================

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    _LOGGER.info(
        "iDM Integration erfolgreich eingerichtet"
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Entfernt die iDM Integration."""

    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )