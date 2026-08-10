import asyncio
import aiohttp
import importlib.util
import os
import sys


# ============================================================
# KONFIGURATION
# ============================================================

ACCESS_TOKEN = "6gYBXPLeiNnEvQJUaiyvh0H6witUbA"
WP_ID = 3419

DIAGRAMS = [
    "graph_system",
    "graph_heat_a",
    "graph_heat_b",
]


# ============================================================
# api.py DIREKT LADEN
#
# Wichtig:
# Wir dürfen nicht schreiben:
#
# from custom_components.idm.api import IDMApi
#
# weil Python dann zuerst __init__.py lädt.
# __init__.py benötigt Home Assistant.
#
# Deshalb laden wir api.py direkt.
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

API_FILE = os.path.join(
    BASE_DIR,
    "custom_components",
    "idm",
    "api.py",
)


spec = importlib.util.spec_from_file_location(
    "idm_api",
    API_FILE,
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        f"api.py konnte nicht geladen werden:\n{API_FILE}"
    )


idm_api = importlib.util.module_from_spec(spec)

sys.modules["idm_api"] = idm_api

spec.loader.exec_module(idm_api)


IDMApi = idm_api.IDMApi


# ============================================================
# EIN DIAGRAMM TESTEN
# ============================================================

async def test_diagram(
    api: IDMApi,
    diagram: str,
) -> None:

    print()
    print("=" * 70)
    print(f"DIAGRAMM: {diagram}")
    print("=" * 70)

    try:

        print()
        print(f"Fordere {diagram} an ...")

        result = await api.get_diagram(
            diagram,
            "24h",
        )

        print()
        print("RESULT KEYS:")
        print(result.keys())

        print()
        print("DIAGRAM:")
        print(result.get("diagram"))

        print()
        print("PERIOD:")
        print(result.get("period"))

        channels = result.get(
            "channels",
            [],
        )

        channel_labels = result.get(
            "channel_labels",
            {},
        )

        data = result.get(
            "data",
            [],
        )

        # ----------------------------------------------------
        # CHANNELS
        # ----------------------------------------------------

        print()
        print("CHANNELS:")
        print("-" * 70)
        print(channels)

        # ----------------------------------------------------
        # CHANNEL LABELS
        # ----------------------------------------------------

        print()
        print("CHANNEL LABELS:")
        print("-" * 70)
        print(channel_labels)

        # ----------------------------------------------------
        # DATENPUNKTE
        # ----------------------------------------------------

        print()
        print("DATENPUNKTE:")
        print("-" * 70)
        print(len(data))

        # ----------------------------------------------------
        # KEINE DATEN
        # ----------------------------------------------------

        if not data:

            print()
            print("KEINE DATENPUNKTE VORHANDEN.")

            return

        # ----------------------------------------------------
        # ERSTER DATENSATZ
        # ----------------------------------------------------

        print()
        print("ERSTER DATENSATZ:")
        print("-" * 70)
        print(data[0])

        # ----------------------------------------------------
        # LETZTER DATENSATZ
        # ----------------------------------------------------

        print()
        print("LETZTER DATENSATZ:")
        print("-" * 70)
        print(data[-1])

        # ----------------------------------------------------
        # KANALÜBERSICHT
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("KANALÜBERSICHT")
        print("=" * 70)

        for channel in channels:

            channel_id = str(channel)

            label = channel_labels.get(
                channel_id,
                "UNBEKANNT",
            )

            first_value = data[0].get(
                channel_id
            )

            last_value = data[-1].get(
                channel_id
            )

            print()
            print(f"Kanal:       {channel_id}")
            print(f"Bezeichnung: {label}")
            print(f"Erster Wert: {first_value}")
            print(f"Letzter Wert: {last_value}")

        # ----------------------------------------------------
        # LETZTE 5 DATENPUNKTE
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("LETZTE 5 DATENPUNKTE")
        print("=" * 70)

        for point in data[-5:]:

            print(point)

    except Exception as err:

        print()
        print("=" * 70)
        print("FEHLER BEI DER ABFRAGE")
        print("=" * 70)

        print()
        print("Fehlertyp:")
        print(type(err).__name__)

        print()
        print("Fehlermeldung:")
        print(str(err))


# ============================================================
# HAUPTPROGRAMM
# ============================================================

async def main() -> None:

    print()
    print("=" * 70)
    print("iDM CHANNEL TEST")
    print("=" * 70)

    print()
    print(f"Wärmepumpe: {WP_ID}")
    print("Zeitraum:   24h")

    print()
    print("Getestete Diagramme:")

    for diagram in DIAGRAMS:

        print(
            f"  - {diagram}"
        )

    print()
    print("=" * 70)

    # --------------------------------------------------------
    # HTTP SESSION
    # --------------------------------------------------------

    async with aiohttp.ClientSession() as session:

        # ----------------------------------------------------
        # IDM API
        # ----------------------------------------------------

        api = IDMApi(
            session=session,
            access_token=ACCESS_TOKEN,
            wp_id=WP_ID,
        )

        # ----------------------------------------------------
        # ALLE DIAGRAMME TESTEN
        # ----------------------------------------------------

        for diagram in DIAGRAMS:

            await test_diagram(
                api,
                diagram,
            )

            # Kleine Pause zwischen den Requests
            await asyncio.sleep(0.5)

    print()
    print("=" * 70)
    print("TEST ABGESCHLOSSEN")
    print("=" * 70)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())