from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)


CHANNELS = {
    "1": (
        "Außentemperatur",
        "°C",
    ),
    "2": (
        "Wärmepumpe Vorlauf",
        "°C",
    ),
    "4": (
        "Wärmequelle Temperatur",
        "°C",
    ),
    "5": (
        "Heizpuffer Temperatur",
        "°C",
    ),
    "6": (
        "Kaltpuffer Temperatur",
        "°C",
    ),
    "7": (
        "Warmwasser unten",
        "°C",
    ),
}


DEVICE_INFO = {
    "identifiers": {
        ("idm", "3419")
    },
    "name": "iDM TERRA S",
    "manufacturer": "iDM",
    "model": "TERRA S",
    "sw_version": "t1.2i1",
}


async def async_setup_entry(
    hass,
    config_entry,
    async_add_entities,
):

    coordinator = config_entry.runtime_data

    entities = []

    graph = coordinator.data.get(
        "graph",
        {}
    )

    data = graph.get(
        "data",
        []
    )

    latest_data = {}

    if data:
        latest_data = data[-1]


    for channel, values in CHANNELS.items():

        # Sensor nur anlegen, wenn die API diesen Kanal liefert
        if channel not in latest_data:
            continue

        entities.append(
            IDMTemperatureSensor(
                coordinator,
                channel,
                values[0],
                values[1],
            )
        )


    entities.extend(
        [
            IDMInfoSensor(
                coordinator,
                "Online",
                "online",
            ),
            IDMInfoSensor(
                coordinator,
                "Modell",
                "wp_type",
            ),
            IDMInfoSensor(
                coordinator,
                "Navigator Version",
                "nav_version",
            ),
        ]
    )


    async_add_entities(
        entities
    )



class IDMTemperatureSensor(
    CoordinatorEntity,
    SensorEntity,
):

    def __init__(
        self,
        coordinator,
        channel,
        name,
        unit,
    ):

        super().__init__(
            coordinator
        )

        self.channel = channel

        self._attr_unique_id = (
            f"idm_3419_temperature_{channel}"
        )

        self._attr_name = (
            f"iDM {name}"
        )

        self._attr_native_unit_of_measurement = unit

        self._attr_device_class = (
            SensorDeviceClass.TEMPERATURE
        )

        self._attr_device_info = DEVICE_INFO



    @property
    def native_value(self):

        graph = self.coordinator.data.get(
            "graph",
            {}
        )

        data = graph.get(
            "data",
            []
        )

        if not data:
            return None


        value = data[-1].get(
            self.channel
        )


        if value is None:
            return None


        return round(
            value,
            1
        )



class IDMInfoSensor(
    CoordinatorEntity,
    SensorEntity,
):

    def __init__(
        self,
        coordinator,
        name,
        key,
    ):

        super().__init__(
            coordinator
        )

        self.key = key

        self._attr_unique_id = (
            f"idm_3419_info_{key}"
        )

        self._attr_name = (
            f"iDM {name}"
        )

        self._attr_device_info = DEVICE_INFO



    @property
    def native_value(self):

        heatpump = (
            self.coordinator.data.get(
                "heatpump",
                {}
            )
        )

        return heatpump.get(
            self.key
        )