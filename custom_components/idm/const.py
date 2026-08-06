"""Constants for the iDM integration."""

from __future__ import annotations


DOMAIN = "idm"

NAME = "iDM myIDM"

MANUFACTURER = "iDM"

MODEL = "myIDM"


# iDM API
#
# Diese URL ist der API-Basis-Endpunkt.
# Der genaue Pfad wird in api.py ergänzt.
API_URL = "https://myidm.at"


DEFAULT_SCAN_INTERVAL = 60


PLATFORMS = [
    "sensor",
]


CONF_INSTALLATION = "installation"


DEVICE_IDENTIFIER = "idm_device"