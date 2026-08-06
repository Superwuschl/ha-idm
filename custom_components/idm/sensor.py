"""Sensor platform for iDM integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature

from .const import DOMAIN
from .entity import IDMEntity
from .sensor_descriptions import SENSOR_DESCRIPTIONS


async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
):
    """Set up iDM sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []

    for description in SENSOR_DESCRIPTIONS:
        entities.append(
            IDMSensor(
                coordinator,
                description,
            )
        )

    async_add_entities(entities)


class IDMSensor(IDMEntity, SensorEntity):
    """Representation of an iDM sensor."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator,
        description,
    ):
        """Initialize sensor."""

        super().__init__(
            coordinator,
            description.key,
        )

        self._description = description

        self._attr_name = description.name

        self._attr_unique_id = (
            f"idm_{description.key}"
        )

        self._attr_icon = description.icon

    @property
    def native_value(self):
        """Return sensor value."""

        value = self.coordinator.data

        for part in self._key.split("."):

            if isinstance(value, list):
                value = value[int(part)]

            elif isinstance(value, dict):
                value = value.get(part)

            else:
                value = None
                break

        if value is None:
            return None

        if isinstance(value, str):
            value = (
                value
                .replace("°C", "")
                .strip()
            )

        try:
            return float(value)

        except (
            ValueError,
            TypeError,
        ):
            return value