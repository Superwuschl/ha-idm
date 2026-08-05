"""Sensor platform for iDM integration."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature

from .const import DOMAIN


SENSORS = {
    "Außentemperatur": "temp_outside",
    "Hygienetemperatur": "temp_hygienic",
    "Wärmepumpe Temperatur": "temp_heat",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up iDM sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []

    for name, key in SENSORS.items():
        entities.append(
            IDMSensor(
                coordinator,
                name,
                key,
            )
        )

    async_add_entities(entities)


class IDMSensor(SensorEntity):
    """Representation of an iDM sensor."""

    def __init__(self, coordinator, name, key):
        self.coordinator = coordinator
        self._attr_name = f"iDM {name}"
        self._key = key

    @property
    def native_value(self):
        """Return sensor value."""

        value = self.coordinator.data.get(self._key)

        if value is None:
            return None

        if isinstance(value, str):
            value = value.replace("°C", "").strip()

        return float(value)

    @property
    def native_unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS

    async def async_update(self):
        """Update data."""

        await self.coordinator.async_request_refresh()