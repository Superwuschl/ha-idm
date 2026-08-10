from __future__ import annotations

import asyncio
import importlib.util

import aiohttp


# ============================================================
# KONFIGURATION
# ============================================================

ACCESS_TOKEN = "OmuGrETkbh9TANzpvY1POv2vDt9kr6"
REFRESH_TOKEN = "Xbd6NT7QUvkOoY8bqHfLzitWM7s15r"

WP_ID = 3419

API_FILE = (
    r"C:\Users\Bernd\Documents\ha-idm"
    r"\custom_components\idm\api.py"
)


# ============================================================
# API LADEN
# ============================================================

spec = importlib.util.spec_from_file_location(
    "idm_api",
    API_FILE,
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        f"API-Datei konnte nicht geladen werden:\n{API_FILE}"
    )

idm_api = importlib.util.module_from_spec(spec)

spec.loader.exec_module(idm_api)

IDMApi = idm_api.IDMApi


# ============================================================
# LETZTEN KANALWERT ERMITTELN
# ============================================================

def last_channel_value(data, channel):

    points = data.get("data", [])

    if not isinstance(points, list):
        return None

    channel = str(channel)

    for point in reversed(points):

        if not isinstance(point, dict):
            continue

        if channel in point:
            return point[channel]

    return None


# ============================================================
# MAIN
# ============================================================

async def main():

    print()
    print("=" * 70)
    print("iDM SENSORWERTE TEST")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:

        api = IDMApi(
            session=session,
            access_token=ACCESS_TOKEN,
            refresh_token=REFRESH_TOKEN,
            wp_id=WP_ID,
        )

        # ====================================================
        # SYSTEM
        # ====================================================

        print()
        print("-" * 70)
        print("SYSTEM")
        print("-" * 70)

        system = await api.get_system_diagram(
            period="24h"
        )

        system_channels = {
            1: "Außentemperatur",
            2: "Wärmepumpe Vorlauf",
            4: "Wärmequelle",
            5: "Wärmepuffer",
            6: "Kaltpuffer",
            7: "Warmwasser unten",
        }

        for channel, name in system_channels.items():

            value = last_channel_value(
                system,
                channel,
            )

            print(
                f"{channel:>3} | "
                f"{name:<25} | "
                f"{value}"
            )

        # ====================================================
        # HEIZKREIS A
        # ====================================================

        print()
        print("-" * 70)
        print("HEIZKREIS A")
        print("-" * 70)

        heat_a = await api.get_heat_a_diagram(
            period="24h"
        )

        heat_a_channels = {
            9: "Vorlauf Heizkreis A",
            99: "Soll-Vorlauf Heizkreis A",
            16: "Raumtemperatur Heizkreis A",
            106: "Soll-Raumtemperatur Heizkreis A",
            123: "Aktiver Modus Heizkreis A",
            130: "Modus Heizkreis A",
        }

        for channel, name in heat_a_channels.items():

            value = last_channel_value(
                heat_a,
                channel,
            )

            print(
                f"{channel:>3} | "
                f"{name:<30} | "
                f"{value}"
            )

        # ====================================================
        # MODUS
        # ====================================================

        print()
        print("-" * 70)
        print("MODUS")
        print("-" * 70)

        mode = await api.get_heat_a_mode()

        print(
            f"Heizkreis A Modus: {mode}"
        )

    print()
    print("=" * 70)
    print("TEST BEENDET")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())