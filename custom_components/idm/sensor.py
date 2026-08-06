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


HEAT_CIRCUIT_A_CHANNELS = {
    "9": (
        "Heizkreis A Vorlauf",
        "°C",
    ),
    "99": (
        "Heizkreis A Soll Vorlauf",
        "°C",
    ),
    "16": (
        "Raumtemperatur",
        "°C",
    ),
    "106": (
        "Soll Raumtemperatur",
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


    #
    # Systemtemperaturen
    #

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

        if channel not in latest_data:
            continue

        entities.append(
            IDMTemperatureSensor(
                coordinator,
                channel,
                values[0],
                values[1],
                "system",
            )
        )


    #
    # Heizkreis A
    #

    heat_a = coordinator.data.get(
        "heat_a",
        {}
    )

    heat_a_data = heat_a.get(
        "data",
        []
    )

    latest_heat_a = {}

    if heat_a_data:
        latest_heat_a = heat_a_data[-1]


    for channel, values in HEAT_CIRCUIT_A_CHANNELS.items():

        if channel not in latest_heat_a:
            continue

        entities.append(
            IDMTemperatureSensor(
                coordinator,
                channel,
                values[0],
                values[1],
                "heat_a",
            )
        )


    #
    # Infos
    #

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
        source,
    ):

        super().__init__(
            coordinator
        )

        self.channel = channel
        self.source = source

        self._attr_unique_id = (
            f"idm_3419_{source}_{channel}"
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

        if self.source == "heat_a":

            graph = self.coordinator.data.get(
                "heat_a",
                {}
            )

        else:

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