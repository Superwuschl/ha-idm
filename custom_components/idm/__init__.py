"""The iDM integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import IDMApi
from .const import DOMAIN, PLATFORMS
from .coordinator import IDMDataUpdateCoordinator


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up iDM from config entry."""

    _LOGGER.debug(
        "Setting up iDM integration"
    )


    api = IDMApi(
        username=entry.data["username"],
        password=entry.data["password"],
        installation=entry.data["installation"],
        access_token=entry.data["access_token"],
    )


    try:

        await api.login()


    except Exception as err:

        _LOGGER.error(
            "iDM login failed: %s",
            err,
        )

        await api.close()

        raise


    coordinator = IDMDataUpdateCoordinator(
        hass,
        api,
    )


    try:

        await coordinator.async_config_entry_first_refresh()


    except Exception as err:

        _LOGGER.error(
            "Unable to fetch iDM data: %s",
            err,
        )

        await api.close()

        raise


    hass.data.setdefault(
        DOMAIN,
        {},
    )


    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }


    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )


    _LOGGER.debug(
        "iDM integration successfully loaded"
    )


    return True



async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload iDM entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )


    if unload_ok:

        data = hass.data[DOMAIN].pop(
            entry.entry_id,
            None,
        )


        if data:

            api = data.get("api")

            if api:

                await api.close()


        _LOGGER.debug(
            "iDM integration unloaded"
        )


    return unload_ok