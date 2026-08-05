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

    _attr_has_entity_name = True

    def __init__(self, coordinator, name, key):
        """Initialize sensor."""

        self.coordinator = coordinator
        self._attr_name = name
        self._key = key

    @property
    def available(self):
        """Return availability."""

        return self.coordinator.last_update_success

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
        """Return unit."""

        return UnitOfTemperature.CELSIUS

    async def async_added_to_hass(self):
        """Register coordinator listener."""

        self.async_on_remove(
            self.coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )