"""Base entity for iDM integration."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    DEVICE_IDENTIFIER,
)


class IDMEntity(CoordinatorEntity):
    """Base class for iDM entities."""

    def __init__(
        self,
        coordinator,
        key: str,
    ) -> None:
        """Initialize entity."""

        super().__init__(coordinator)

        self._key = key

    @property
    def device_info(self):
        """Return device information."""

        return {
            "identifiers": {
                (
                    DOMAIN,
                    DEVICE_IDENTIFIER,
                )
            },
            "name": "iDM Wärmepumpe",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }