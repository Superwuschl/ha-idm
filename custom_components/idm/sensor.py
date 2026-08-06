from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)


DEVICE_INFO = {
    "identifiers": {
        ("idm", "3419")
    },
    "name": "iDM TERRA S",
    "manufacturer": "iDM",
    "model": "TERRA S",
}


SYSTEM_SENSORS = {
    "1": (
        "idm_aussentemperatur",
        "Außentemperatur",
    ),
    "2": (
        "idm_warmepumpe_vorlauf",
        "Wärmepumpe Vorlauf",
    ),
    "4": (
        "idm_warmequelle_temperatur",
        "Wärmequelle Temperatur",
    ),
    "5": (
        "idm_heizpuffer_temperatur",
        "Heizpuffer Temperatur",
    ),
    "7": (
        "idm_warmwasser_unten",
        "Warmwasser unten",
    ),
}


HEAT_A_SENSORS = {
    "9": (
        "idm_heizkreis_a_vorlauf",
        "Heizkreis A Vorlauf",
    ),
    "99": (
        "idm_heizkreis_a_soll_vorlauf",
        "Heizkreis A Soll Vorlauf",
    ),
    "106": (
        "idm_heizkreis_a_soll_raumtemperatur",
        "Heizkreis A Soll Raumtemperatur",
    ),
}


async def async_setup_entry(
    hass,
    config_entry,
    async_add_entities,
):

    coordinator = config_entry.runtime_data

    entities = []


    for channel, values in SYSTEM_SENSORS.items():

        entities.append(
            IDMGraphSensor(
                coordinator,
                "graph",
                channel,
                values[0],
                values[1],
            )
        )


    for channel, values in HEAT_A_SENSORS.items():

        entities.append(
            IDMGraphSensor(
                coordinator,
                "heat_a",
                channel,
                values[0],
                values[1],
            )
        )


    entities.extend(
        [
            IDMInfoSensor(
                coordinator,
                "online",
                "Online",
            ),

            IDMInfoSensor(
                coordinator,
                "wp_type",
                "Modell",
            ),

            IDMInfoSensor(
                coordinator,
                "nav_version",
                "Navigator Version",
            ),
        ]
    )


    async_add_entities(
        entities
    )



class IDMGraphSensor(
    CoordinatorEntity,
    SensorEntity,
):

    def __init__(
        self,
        coordinator,
        source,
        channel,
        unique_id,
        name,
    ):

        super().__init__(
            coordinator
        )

        self.source = source
        self.channel = channel

        self._attr_unique_id = unique_id
        self._attr_name = name

        self._attr_device_info = DEVICE_INFO

        self._attr_native_unit_of_measurement = "°C"

        self._attr_device_class = (
            SensorDeviceClass.TEMPERATURE
        )


    @property
    def native_value(self):

        graph = self.coordinator.data.get(
            self.source,
            {}
        )

        data = graph.get(
            "data",
            []
        )


        if not data:
            return None


        value = data[-1].get(
            str(self.channel)
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
        key,
        name,
    ):

        super().__init__(
            coordinator
        )

        self.key = key

        self._attr_unique_id = (
            f"idm_{key}"
        )

        self._attr_name = name

        self._attr_device_info = DEVICE_INFO


    @property
    def native_value(self):

        heatpump = self.coordinator.data.get(
            "heatpump",
            {}
        )

        return heatpump.get(
            self.key
        )