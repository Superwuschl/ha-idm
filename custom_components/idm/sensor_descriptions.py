"""Sensor descriptions for iDM integration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IDMSensorDescription:
    """Describe an iDM sensor."""

    name: str
    key: str
    icon: str


SENSOR_DESCRIPTIONS = (

    IDMSensorDescription(
        name="Außentemperatur",
        key="temp_outside",
        icon="mdi:thermometer",
    ),

    IDMSensorDescription(
        name="Hygienetemperatur",
        key="temp_hygienic",
        icon="mdi:water-thermometer",
    ),

    IDMSensorDescription(
        name="Wärmepumpe Temperatur",
        key="temp_heat",
        icon="mdi:heat-pump",
    ),

    IDMSensorDescription(
        name="Heizkreis Vorlauf",
        key="circuits.0.temp_forerun_actual",
        icon="mdi:thermometer-chevron-up",
    ),

    IDMSensorDescription(
        name="Heizkreis Soll Normal",
        key="circuits.0.temp_params_normal.value",
        icon="mdi:thermometer-check",
    ),

    IDMSensorDescription(
        name="Heizkreis Soll Eco",
        key="circuits.0.temp_params_eco.value",
        icon="mdi:leaf-thermometer",
    ),
)