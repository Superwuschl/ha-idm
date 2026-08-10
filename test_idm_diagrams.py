from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

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
# HA-UNABHÄNGIGER API-TEST
# ============================================================

async def main():

    print()
    print("=" * 80)
    print("iDM DIAGRAMM-STRUKTURTEST")
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

    async with __import__("aiohttp").ClientSession() as session:

        api = IDMApi(
            session,
            ACCESS_TOKEN,
            REFRESH_TOKEN,
            WP_ID,
        )

        # ====================================================
        # 1. VERFÜGBARE DIAGRAMME
        # ====================================================

        print()
        print("=" * 80)
        print("1. VERFÜGBARE DIAGRAMME")
        print("=" * 80)

        endpoint = f"/heatpumps/{WP_ID}/diagrams/"

        try:

            result = await api.get(endpoint)

            print()
            print("HTTP / API erfolgreich")

            print()
            print("RAW RESPONSE:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            print()
            print("DATENTYP:")
            print(type(result).__name__)

            if isinstance(result, dict):

                diagrams = result.get("diagrams")

                print()
                print("ANZAHL DIAGRAMME:")
                print(len(diagrams) if isinstance(diagrams, list) else "UNBEKANNT")

                print()
                print("DIAGRAMME:")

                if isinstance(diagrams, list):

                    for index, diagram in enumerate(diagrams):

                        print()
                        print("-" * 60)
                        print(f"DIAGRAMM {index}")
                        print("-" * 60)

                        print(json.dumps(
                            diagram,
                            indent=2,
                            ensure_ascii=False,
                        ))

                else:

                    print("Keine Liste gefunden.")

        except Exception as err:

            print()
            print("FEHLER BEIM AUSLESEN DER DIAGRAMME:")
            print(type(err).__name__)
            print(err)

            return

        # ====================================================
        # 2. VERSUCHE DIE GEFUNDENEN DIAGRAMME ABZURUFEN
        # ====================================================

        if not isinstance(result, dict):
            return

        diagrams = result.get("diagrams")

        if not isinstance(diagrams, list):
            return

        print()
        print("=" * 80)
        print("2. DIAGRAMM-ENDPOINTS")
        print("=" * 80)

        for index, diagram in enumerate(diagrams):

            print()
            print("-" * 80)
            print(f"DIAGRAMM {index}")
            print("-" * 80)

            print("RAW:")
            print(json.dumps(
                diagram,
                indent=2,
                ensure_ascii=False,
            ))

            # Wir suchen mögliche Namen/IDs aus der Antwort.
            candidates = []

            if isinstance(diagram, dict):

                for key in (
                    "id",
                    "name",
                    "key",
                    "slug",
                    "diagram",
                    "endpoint",
                    "url",
                ):

                    value = diagram.get(key)

                    if value is not None:
                        candidates.append((key, value))

            print()
            print("GEFUNDENE IDENTIFIER:")

            for key, value in candidates:
                print(f"{key}: {value}")

        print()
        print("=" * 80)
        print("TEST BEENDET")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())