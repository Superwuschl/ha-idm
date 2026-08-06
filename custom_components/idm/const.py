"""Constants for the iDM integration."""

from datetime import timedelta

DOMAIN = "idm"

NAME = "iDM myIDM"

MANUFACTURER = "iDM"

DEFAULT_SCAN_INTERVAL = 60

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

API_URL = "https://myidm.at"

PLATFORMS = [
    "sensor",
]

CONF_INSTALLATION = "installation"

DEVICE_IDENTIFIER = "main"

ATTR_TEMPERATURE = "temperature"