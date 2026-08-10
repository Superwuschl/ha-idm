from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import aiohttp


# ============================================================
# PROJEKT
# ============================================================

PROJECT_DIR = Path(r"C:\Users\Bernd\Documents\ha-idm")
API_DIR = PROJECT_DIR / "custom_components" / "idm"

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))


from api import IDMApi


# ============================================================
# KONFIGURATION
# ============================================================

ACCESS_TOKEN = "OmuGrETkbh9TANzpvY1POv2vDt9kr6"
REFRESH_TOKEN = "Xbd6NT7QUvkOoY8bqHfLzitWM7s15r"
WP_ID = 3419


# ============================================================
# TEST
# ============================================================

async def main():

    print()
    print("=" * 80)
    print("iDM GRAPH_HEAT_A TEST")
    print("=" * 80)

    print()
    print("Projekt:")
    print(PROJECT_DIR)

    print()
    print("API:")
    print(API_DIR)

    print()
    print("Wärmepumpe:")
    print(WP_ID)

    endpoint = f"/heatpumps/{WP_ID}/diagrams/graph_heat_a/"

    print()
    print("ENDPOINT:")
    print(endpoint)

    print()
    print("PARAMETER:")
    print({
        "period": "30d"
    })

    async with aiohttp.ClientSession() as session:

        api = IDMApi(
            session,
            ACCESS_TOKEN,
            REFRESH_TOKEN,
            WP_ID,
        )

        try:

            result = await api.get(
                endpoint,
                params={
                    "period": "30d"
                },
            )

            print()
            print("=" * 80)
            print("HTTP / API ERFOLGREICH")
            print("=" * 80)

            print()
            print("DATENTYP:")
            print(type(result).__name__)

            print()
            print("KEYS:")

            if isinstance(result, dict):
                print(list(result.keys()))

            print()
            print("RAW RESPONSE:")
            print(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False,
                )
            )

            # =================================================
            # STRUKTUR
            # =================================================

            if isinstance(result, dict):

                print()
                print("=" * 80)
                print("STRUKTUR")
                print("=" * 80)

                for key, value in result.items():

                    print()

                    if isinstance(value, list):

                        print(
                            f"{key}: list "
                            f"({len(value)} items)"
                        )

                    elif isinstance(value, dict):

                        print(
                            f"{key}: dict "
                            f"({len(value)} keys)"
                        )

                    else:

                        print(
                            f"{key}: "
                            f"{type(value).__name__} = "
                            f"{value!r}"
                        )

                # =============================================
                # CHANNELS
                # =============================================

                channels = result.get("channels")

                if channels is not None:

                    print()
                    print("=" * 80)
                    print("CHANNELS")
                    print("=" * 80)

                    print(channels)

                # =============================================
                # CHANNEL LABELS
                # =============================================

                labels = result.get("channel_labels")

                if labels is not None:

                    print()
                    print("=" * 80)
                    print("CHANNEL LABELS")
                    print("=" * 80)

                    print(
                        json.dumps(
                            labels,
                            indent=2,
                            ensure_ascii=False,
                        )
                    )

                # =============================================
                # DATA
                # =============================================

                data = result.get("data")

                if isinstance(data, list):

                    print()
                    print("=" * 80)
                    print("DATENPUNKTE")
                    print("=" * 80)

                    print("Anzahl:")
                    print(len(data))

                    if data:

                        print()
                        print("ERSTER DATENPUNKT:")

                        print(
                            json.dumps(
                                data[0],
                                indent=2,
                                ensure_ascii=False,
                            )
                        )

                        print()
                        print("LETZTER DATENPUNKT:")

                        print(
                            json.dumps(
                                data[-1],
                                indent=2,
                                ensure_ascii=False,
                            )
                        )

                        # =====================================
                        # TATSÄCHLICHE FELDER
                        # =====================================

                        fields = set()

                        for point in data:

                            if isinstance(point, dict):
                                fields.update(point.keys())

                        print()
                        print("=" * 80)
                        print("TATSÄCHLICHE DATENFELDER")
                        print("=" * 80)

                        print(
                            sorted(
                                fields,
                                key=str
                            )
                        )

        except Exception as err:

            print()
            print("=" * 80)
            print("FEHLER")
            print("=" * 80)

            print()
            print("FEHLERTYP:")
            print(type(err).__name__)

            print()
            print("FEHLER:")
            print(err)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())