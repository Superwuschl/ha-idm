from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import aiohttp


# ============================================================
# PROJEKT / API
# ============================================================

PROJECT_DIR = Path(r"C:\Users\Bernd\Documents\ha-idm")
API_DIR = PROJECT_DIR / "custom_components" / "idm"

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from api import IDMApi


# ============================================================
# KONFIGURATION
# ============================================================

ACCESS_TOKEN = "6gYBXPLeiNnEvQJUaiyvh0H6witUbA"
REFRESH_TOKEN = "Gd5hSzSg5zJHXOemqUwCMvo7EahN3s"

WP_ID = 3419

PERIOD = "24h"


# ============================================================
# GETESTETE KANÄLE
# ============================================================

CHANNELS = {
    "130": "Heizkreis A Modus",
    "99": "Heizkreis A aktiv",
    "9": "Heizkreis A Vorlauf",
    "106": "Heizkreis A Soll Vorlauf",
    "123": "Heizkreis A Raum",
}


# ============================================================
# HILFSFUNKTION
# ============================================================

def print_value(channel: str, value):
    name = CHANNELS.get(channel, "Unbekannt")

    print()
    print(f"Kanal {channel}")
    print(f"Bezeichnung : {name}")
    print(f"Rohwert     : {value}")

    # --------------------------------------------------------
    # Bekannte Kanalinterpretationen
    # --------------------------------------------------------

    if channel == "130":
        try:
            mode = int(float(value))

            modes = {
                0: "Aus",
                1: "Zeitprogramm",
                2: "Normal",
                3: "Eco",
                4: "Manuell Heizen",
                5: "Manuell Kühlen",
            }

            print(f"Interpretation: {modes.get(mode, 'Unbekannt')}")

        except (TypeError, ValueError):
            print("Interpretation: ungültiger Moduswert")

    elif channel == "99":
        try:
            numeric = float(value)
            print(f"Interpretation: {'AKTIV' if numeric else 'INAKTIV'}")

        except (TypeError, ValueError):
            print("Interpretation: nicht numerisch")

    elif channel in ("9", "106", "123"):
        try:
            print(f"Interpretation: {float(value):.2f} °C")

        except (TypeError, ValueError):
            print("Interpretation: nicht numerisch")


# ============================================================
# HAUPTTEST
# ============================================================

async def main():

    print()
    print("=" * 80)
    print("iDM API – GEZIELTER TEST GRAPH_HEAT_A")
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

    print()
    print("Diagramm:")
    print("graph_heat_a")

    print()
    print("Periode:")
    print(PERIOD)

    print()
    print("=" * 80)

    async with aiohttp.ClientSession() as session:

        api = IDMApi(
            session,
            ACCESS_TOKEN,
            REFRESH_TOKEN,
            WP_ID,
        )

        try:

            # ------------------------------------------------
            # DIREKTER AUFRUF ÜBER DIE VORHANDENE API-METHODE
            # ------------------------------------------------

            result = await api.get_heat_a_graph(PERIOD)

            print()
            print("=" * 80)
            print("API-ANTWORT")
            print("=" * 80)

            if not isinstance(result, dict):
                print("FEHLER: API-Antwort ist kein Dictionary.")
                print(repr(result))
                return

            print()
            print("Keys:")
            print(list(result.keys()))

            print()
            print("Diagram:")
            print(result.get("diagram"))

            print()
            print("Period:")
            print(result.get("period"))

            print()
            print("Channels:")
            print(result.get("channels"))

            print()
            print("Channel Labels:")
            print(result.get("channel_labels"))

            data = result.get("data", [])

            print()
            print("Anzahl Datenpunkte:")
            print(len(data) if isinstance(data, list) else 0)

            if not isinstance(data, list) or not data:
                print()
                print("=" * 80)
                print("KEINE DATENPUNKTE")
                print("=" * 80)
                return

            # ------------------------------------------------
            # LETZTEN DATENPUNKT AUSWERTEN
            # ------------------------------------------------

            last = data[-1]

            print()
            print("=" * 80)
            print("LETZTER DATENPUNKT")
            print("=" * 80)

            print()
            print(json.dumps(
                last,
                indent=4,
                ensure_ascii=False,
            ))

            # ------------------------------------------------
            # DIE KANÄLE EINZELN AUSWERTEN
            # ------------------------------------------------

            print()
            print("=" * 80)
            print("KANAL-AUSWERTUNG")
            print("=" * 80)

            for channel, name in CHANNELS.items():

                print()
                print("-" * 80)

                if channel in last:
                    print_value(
                        channel,
                        last[channel],
                    )
                else:
                    print(f"Kanal {channel}")
                    print(f"Bezeichnung : {name}")
                    print("STATUS      : NICHT VORHANDEN")

            # ------------------------------------------------
            # ALLE TATSÄCHLICH GELIEFERTEN KANÄLE
            # ------------------------------------------------

            print()
            print("=" * 80)
            print("ALLE KANÄLE DES LETZTEN DATENPUNKTES")
            print("=" * 80)

            for key, value in last.items():

                if key in (
                    "index",
                    "timestamp",
                    "datetime",
                ):
                    continue

                print(f"{key:>5} : {value}")

            # ------------------------------------------------
            # FEHLENDE KANÄLE
            # ------------------------------------------------

            print()
            print("=" * 80)
            print("PRÜFUNG DER ERWARTETEN KANÄLE")
            print("=" * 80)

            for channel, name in CHANNELS.items():

                if channel in last:
                    print(
                        f"[OK]      Kanal {channel:>3} "
                        f"- {name}"
                    )
                else:
                    print(
                        f"[FEHLT]   Kanal {channel:>3} "
                        f"- {name}"
                    )

            # ------------------------------------------------
            # ROHDATEN ZUR WEITEREN ANALYSE
            # ------------------------------------------------

            print()
            print("=" * 80)
            print("ERSTER UND LETZTER DATENPUNKT")
            print("=" * 80)

            print()
            print("ERSTER:")
            print(json.dumps(
                data[0],
                indent=4,
                ensure_ascii=False,
            ))

            print()
            print("LETZTER:")
            print(json.dumps(
                data[-1],
                indent=4,
                ensure_ascii=False,
            ))

            print()
            print("=" * 80)
            print("TEST ABGESCHLOSSEN")
            print("=" * 80)

        except Exception as err:

            print()
            print("=" * 80)
            print("FEHLER BEIM API-ABRUF")
            print("=" * 80)

            print()
            print(type(err).__name__)
            print(str(err))


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())