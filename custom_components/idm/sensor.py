"""Sensor platform for iDM integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import IDMEntity


SENSORS = {
    "Außentemperatur": {
        "key": "temp_outside",
        "icon": "mdi:thermometer",
    },
    "Hygienetemperatur": {
        "key": "temp_hygienic",
        "icon": "mdi:water-thermometer",
    },
    "Wärmepumpe Temperatur": {
        "key": "temp_heat",
        "icon": "mdi:heat-pump",
    },
    "Heizkreis Vorlauf": {
        "key": "circuits.0.temp_forerun_actual",
        "icon": "mdi:thermometer-chevron-up",
    },
    "Heizkreis Soll Normal": {
        "key": "circuits.0.temp_params_normal.value",
        "icon": "mdi:thermometer-check",
    },
    "Heizkreis Soll Eco": {
        "key": "circuits.0.temp_params_eco.value",
        "icon": "mdi:leaf-thermometer",
    },
}


async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
):
    """Set up iDM sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []

    for name, config in SENSORS.items():
        entities.append(
            IDMSensor(
                coordinator,
                name,
                config["key"],
                config["icon"],
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
        name,
        key,
        icon,
    ):
        """Initialize sensor."""

        super().__init__(
            coordinator,
            key,
        )

        self._attr_name = name
        self._attr_unique_id = f"idm_{key}"
        self._attr_icon = icon

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
            value = value.replace(
                "°C",
                "",
            ).strip()

        try:
            return float(value)

        except (ValueError, TypeError):
            return value