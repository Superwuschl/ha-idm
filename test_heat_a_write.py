import asyncio
import logging
import sys
import types
from pathlib import Path


# ============================================================
# PFAD ZUR iDM INTEGRATION
# ============================================================

BASE_PATH = Path(__file__).resolve().parent

IDM_PATH = (
    BASE_PATH
    / "custom_components"
    / "idm"
)

sys.path.insert(0, str(IDM_PATH))


# ============================================================
# HOME ASSISTANT STUB
# ============================================================

homeassistant_module = types.ModuleType("homeassistant")
homeassistant_core_module = types.ModuleType(
    "homeassistant.core"
)


class HomeAssistant:
    pass


homeassistant_core_module.HomeAssistant = HomeAssistant

sys.modules["homeassistant"] = homeassistant_module
sys.modules["homeassistant.core"] = (
    homeassistant_core_module
)


# ============================================================
# iDM API
# ============================================================

from api import IDMApi


# ============================================================
# EINSTELLUNGEN
# ============================================================

ACCESS_TOKEN = "YhJ8d9HbuExj7ecOzS07KKxiEOmbNV"

WP_ID = 3419


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.WARNING,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s: "
        "%(message)s"
    ),
)


# ============================================================
# TEST
# ============================================================

async def main():

    api = IDMApi(
        hass=None,
        access_token=ACCESS_TOKEN,
        wp_id=WP_ID,
    )

    try:

        print()
        print("========================================")
        print("iDM HEIZKREIS A SCHREIBTEST")
        print("========================================")
        print()
        print("WP-ID:", WP_ID)
        print()
        print("Setze Heizkreis A auf ECO (3)")
        print()

        result = await api.set_heat_a_mode(3)

        print()
        print("========================================")
        print("ERGEBNIS")
        print("========================================")
        print()

        print(result)

        print()
        print("========================================")
        print("TEST BEENDET")
        print("========================================")
        print()

    except Exception as err:

        print()
        print("========================================")
        print("FEHLER")
        print("========================================")
        print()

        print(type(err).__name__)
        print(err)

    finally:

        await api.close()


# ============================================================
# START
# ============================================================

asyncio.run(main())