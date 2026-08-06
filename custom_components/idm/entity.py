"""Base entity for iDM."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class IDMEntity(CoordinatorEntity):
    """Base iDM entity."""

    def __init__(self, coordinator, key):
        """Initialize."""

        super().__init__(coordinator)

        self._key = key

    @property
    def device_info(self):
        """Return device information."""

        return {
            "identifiers": {(DOMAIN, "main")},
            "manufacturer": "iDM",
            "name": "iDM Wärmepumpe",
            "model": "myIDM",
        }

    @property
    def available(self):
        return self.coordinator.last_update_success