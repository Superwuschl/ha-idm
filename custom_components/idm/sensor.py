from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
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


HEAT_A_INFO = {
    "123": (
        "idm_heizkreis_a_aktiv",
        "Heizkreis A aktiv",
    ),
    "130": (
        "idm_heizkreis_a_modus",
        "Heizkreis A Modus",
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


    for channel, values in HEAT_A_INFO.items():

        entities.append(
            IDMGraphSensor(
                coordinator,
                "heat_a",
                channel,
                values[0],
                values[1],
                False,
            )
        )


    entities.extend(
        [
            IDMInfoSensor(coordinator, "online", "Online"),
            IDMInfoSensor(coordinator, "wp_type", "Modell"),
            IDMInfoSensor(coordinator, "nav_version", "Navigator Version"),
            IDMInfoSensor(coordinator, "serialnumber", "Seriennummer"),
            IDMInfoSensor(coordinator, "wp_id", "Wärmepumpe ID"),
            IDMInfoSensor(coordinator, "myidm_id", "myIDM ID"),
            IDMInfoSensor(coordinator, "last_online", "Letzte Verbindung"),
            IDMInfoSensor(coordinator, "logfreq", "Log Intervall"),
        ]
    )


    async_add_entities(entities)



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
        temperature=True,
    ):

        super().__init__(coordinator)

        self.source = source
        self.channel = channel

        self._attr_unique_id = unique_id
        self._attr_name = name
        self._attr_device_info = DEVICE_INFO

        if temperature:

            self._attr_native_unit_of_measurement = "°C"
            self._attr_device_class = (
                SensorDeviceClass.TEMPERATURE
            )
            self._attr_state_class = (
                SensorStateClass.MEASUREMENT
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


        if isinstance(value, float):

            return round(value, 1)


        return value



    @property
    def extra_state_attributes(self):

        graph = self.coordinator.data.get(
            self.source,
            {}
        )

        data = graph.get(
            "data",
            []
        )

        if not data:
            return {}


        last = data[-1]

        return {
            "quelle": self.source,
            "kanal": self.channel,
            "zeitpunkt": last.get("datetime"),
            "diagramm": graph.get("diagram"),
            "periode": graph.get("period"),
        }



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

        super().__init__(coordinator)

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