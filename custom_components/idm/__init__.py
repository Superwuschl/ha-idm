"""iDM myIDM integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import IDMApi
from .const import DOMAIN
from .coordinator import IDMDataUpdateCoordinator


PLATFORMS = [
    "sensor",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up iDM from a config entry."""

    api = IDMApi(
        entry.data["username"],
        entry.data["password"],
    )

    await api.login()

    coordinator = IDMDataUpdateCoordinator(
        hass,
        api,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload iDM."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok