"""Constants for the iDM integration."""

from __future__ import annotations

from datetime import timedelta


DOMAIN = "idm"

NAME = "iDM myIDM"

MANUFACTURER = "iDM"

MODEL = "myIDM"


# API configuration
#
# Diese Adresse wird von der iDM myIDM API verwendet.
# Falls deine alte Integration eine andere URL benutzt hat,
# wird nur diese Zeile angepasst.
API_URL = "https://www.myiDM.at"


# Update interval
DEFAULT_SCAN_INTERVAL = 60

UPDATE_INTERVAL = timedelta(
    seconds=DEFAULT_SCAN_INTERVAL
)


# Platforms loaded by the integration
PLATFORMS = [
    "sensor",
]


# Config entry keys
CONF_INSTALLATION = "installation"


# Device information
DEVICE_IDENTIFIER = "idm_device"