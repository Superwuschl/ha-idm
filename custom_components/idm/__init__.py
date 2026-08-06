from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import IDMApi
from .coordinator import IDMCoordinator

from .const import DOMAIN


PLATFORMS = [
    "sensor",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
):

    access_token = entry.data["access_token"]

    refresh_token = entry.data.get(
        "refresh_token"
    )

    wp_id = entry.data["wp_id"]


    api = IDMApi(
        hass,
        access_token,
        refresh_token,
        wp_id,
    )


    coordinator = IDMCoordinator(
        hass,
        api,
    )


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