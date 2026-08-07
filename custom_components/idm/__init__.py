from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IDMApi
from .coordinator import IDMCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):

    session = async_get_clientsession(hass)

    api = IDMApi(
        session,
        entry.data["access_token"],
        entry.data.get("refresh_token"),
        entry.data["wp_id"],
    )

    coordinator = IDMCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
):
    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )