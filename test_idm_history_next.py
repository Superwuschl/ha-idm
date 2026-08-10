from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import aiohttp


# ============================================================
# PROJEKT- UND API-PFAD
# ============================================================

# Tatsächliche Projektstruktur:
#
# C:\Users\Bernd\Documents\ha-idm\
#
# ├── test_idm_history_next.py
# │
# └── custom_components\
#     └── idm\
#         └── api.py
#
# Diese Datei liegt direkt im Projektverzeichnis.

TEST_FILE = Path(__file__).resolve()

PROJECT_DIR = TEST_FILE.parent

IDM_DIR = PROJECT_DIR / "custom_components" / "idm"

API_FILE = IDM_DIR / "api.py"


print()
print("=" * 100)
print("iDM LOG HISTORY ANALYSE")
print("=" * 100)

print()
print("Testdatei:")
print(TEST_FILE)

print()
print("Projektverzeichnis:")
print(PROJECT_DIR)

print()
print("API-Verzeichnis:")
print(IDM_DIR)

print()
print("api.py:")
print(API_FILE)


# ============================================================
# PRÜFEN, OB PROJEKTVERZEICHNIS STIMMT
# ============================================================

if not PROJECT_DIR.exists():

    print()
    print("=" * 100)
    print("FEHLER: PROJEKTVERZEICHNIS NICHT GEFUNDEN")
    print("=" * 100)

    print()
    print("Gesuchtes Verzeichnis:")
    print(PROJECT_DIR)

    raise SystemExit(1)


# ============================================================
# PRÜFEN, OB API-ORDNER EXISTIERT
# ============================================================

if not IDM_DIR.exists():

    print()
    print("=" * 100)
    print("FEHLER: API-ORDNER NICHT GEFUNDEN")
    print("=" * 100)

    print()
    print("Gesuchter Ordner:")
    print(IDM_DIR)

    print()
    print("Erwartete Struktur:")
    print(PROJECT_DIR / "custom_components" / "idm")

    raise SystemExit(1)


# ============================================================
# PRÜFEN, OB api.py EXISTIERT
# ============================================================

if not API_FILE.exists():

    print()
    print("=" * 100)
    print("FEHLER: api.py NICHT GEFUNDEN")
    print("=" * 100)

    print()
    print("Gesuchte Datei:")
    print(API_FILE)

    raise SystemExit(1)


# ============================================================
# API-ORDNER IN PYTHON-PFAD EINTRAGEN
# ============================================================

if str(IDM_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(IDM_DIR),
    )

print()
print("Python Import-Pfad wurde erweitert:")
print(IDM_DIR)


# ============================================================
# iDM API IMPORT
# ============================================================

try:

    from api import IDMApi

except Exception as err:

    print()
    print("=" * 100)
    print("FEHLER BEIM IMPORT VON api.py")
    print("=" * 100)

    print()
    print("API-Ordner:")
    print(IDM_DIR)

    print()
    print("api.py:")
    print(API_FILE)

    print()
    print("Python sys.path:")

    for path in sys.path:
        print("  ", path)

    print()
    print("Fehler:")
    print(repr(err))

    raise


print()
print("IDMApi erfolgreich importiert.")


# ============================================================
# KONFIGURATION
# ============================================================

ACCESS_TOKEN = "OmuGrETkbh9TANzpvY1POv2vDt9kr6"

REFRESH_TOKEN = "Xbd6NT7QUvkOoY8bqHfLzitWM7s15r"

WP_ID = 3419


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def print_separator(title: str) -> None:

    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def print_result(result) -> None:

    print("-" * 100)

    if isinstance(result, dict):

        print(
            f"dict ({len(result)} keys)"
        )

        for key, value in result.items():

            if isinstance(value, dict):

                print(
                    f"  {key}: dict "
                    f"({len(value)} keys)"
                )

            elif isinstance(value, list):

                print(
                    f"  {key}: list "
                    f"({len(value)} items)"
                )

            else:

                print(
                    f"  {key}: "
                    f"{type(value).__name__} = "
                    f"{value!r}"
                )

        data = result.get("data")

        if isinstance(data, list) and data:

            print()
            print(
                f"  Datenpunkte: {len(data)}"
            )

            print()
            print("  ERSTER DATENSATZ:")
            print(data[0])

            print()
            print("  LETZTER DATENSATZ:")
            print(data[-1])

    else:

        print(
            type(result).__name__
        )

        print(result)


def print_log_summary(result) -> None:

    print("-" * 100)

    if not isinstance(result, dict):

        print("Unerwarteter Antworttyp:")
        print(type(result).__name__)
        print(result)

        return

    print()
    print("LOG-ANTWORT:")

    print(
        f"count:          {result.get('count')}"
    )

    print(
        f"recordsTotal:   {result.get('recordsTotal')}"
    )

    print(
        f"recordsFiltered:{result.get('recordsFiltered')}"
    )

    print(
        f"previous:       {result.get('previous')}"
    )

    print(
        f"next:           {result.get('next')}"
    )

    results = result.get("results")

    if not isinstance(results, list):

        print()
        print("Keine results-Liste vorhanden.")

        return

    print()
    print(
        f"RESULTS: {len(results)}"
    )

    if not results:

        print("Keine Logeinträge vorhanden.")

        return

    print()
    print("ERSTER LOGEINTRAG:")
    print(results[0])

    print()
    print("LETZTER LOGEINTRAG:")
    print(results[-1])

    print()
    print("ALLE FELDER DES ERSTEN LOGEINTRAGS:")

    first = results[0]

    if isinstance(first, dict):

        for key, value in first.items():

            print(
                f"  {key}: "
                f"{type(value).__name__} = "
                f"{value!r}"
            )


# ============================================================
# HAUPTTEST
# ============================================================

async def main() -> None:

    print_separator(
        "iDM LOG HISTORY ANALYSE"
    )

    print()
    print("Testdatei:")
    print(TEST_FILE)

    print()
    print("Projektverzeichnis:")
    print(PROJECT_DIR)

    print()
    print("api.py Ordner:")
    print(IDM_DIR)

    print()
    print("api.py:")
    print(API_FILE)

    print()
    print(
        f"Wärmepumpe: {WP_ID}"
    )

    print()
    print(
        "API: https://a.myidm.at/api/v1"
    )

    print()
    print(
        "IDMApi erfolgreich importiert."
    )


    # ========================================================
    # TOKEN PRÜFEN
    # ========================================================

    if not ACCESS_TOKEN:

        print()
        print(
            "FEHLER: ACCESS_TOKEN ist leer."
        )

        return


    # ========================================================
    # HTTP SESSION
    # ========================================================

    timeout = aiohttp.ClientTimeout(
        total=30
    )

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:

        api = IDMApi(
            session=session,
            access_token=ACCESS_TOKEN,
            refresh_token=REFRESH_TOKEN,
            wp_id=WP_ID,
        )


        # ====================================================
        # 1. HEATPUMP ROOT
        # ====================================================

        print_separator(
            "1. HEATPUMP ROOT"
        )

        try:

            result = await api.get_heatpump()

            print_result(result)

        except Exception as err:

            print()
            print("FEHLER:")
            print(repr(err))


        # ====================================================
        # 2. SYSTEM DIAGRAM
        # ====================================================

        print_separator(
            "2. SYSTEM DIAGRAM"
        )

        try:

            result = await api.get_system_diagram(
                period="30d"
            )

            print_result(result)

        except Exception as err:

            print()
            print("FEHLER:")
            print(repr(err))


        # ====================================================
        # 3. PERIODEN TESTEN
        # ====================================================

        print_separator(
            "3. PERIOD TEST"
        )

        periods = [
            "1h",
            "6h",
            "12h",
            "24h",
            "7d",
            "30d",
            "90d",
            "365d",
        ]

        for period in periods:

            print()
            print(
                f"TEST PERIOD: {period}"
            )

            try:

                result = await api.get_system_diagram(
                    period=period
                )

                if isinstance(result, dict):

                    returned_period = result.get(
                        "period"
                    )

                    data = result.get(
                        "data",
                        []
                    )

                    print(
                        f"API PERIOD: "
                        f"{returned_period}"
                    )

                    print(
                        f"PUNKTE: "
                        f"{len(data) if isinstance(data, list) else '???'}"
                    )

                    if (
                        isinstance(data, list)
                        and data
                    ):

                        print("ERSTER:")
                        print(data[0])

                        print("LETZTER:")
                        print(data[-1])

                else:

                    print(result)

            except Exception as err:

                print(
                    f"FEHLER: {err}"
                )


        # ====================================================
        # 4. DIREKTER GRAPH_SYSTEM TEST
        # ====================================================

        print_separator(
            "4. DIREKTER GRAPH_SYSTEM TEST"
        )

        try:

            result = await api.get(
                f"/heatpumps/{WP_ID}"
                "/diagrams/graph_system/",
                params={
                    "period": "30d",
                },
            )

            print_result(result)

        except Exception as err:

            print()
            print("FEHLER:")
            print(repr(err))


        # ====================================================
        # 5. ZEITPARAMETER
        # ====================================================

        print_separator(
            "5. ZEITPARAMETER TEST"
        )

        parameter_sets = [

            {
                "period": "30d",
                "start": "2026-07-01",
                "end": "2026-08-09",
            },

            {
                "period": "30d",
                "from": "2026-07-01",
                "to": "2026-08-09",
            },

            {
                "period": "30d",
                "start_date": "2026-07-01",
                "end_date": "2026-08-09",
            },

            {
                "period": "30d",
                "date_from": "2026-07-01",
                "date_to": "2026-08-09",
            },

            {
                "period": "30d",
                "from_date": "2026-07-01",
                "to_date": "2026-08-09",
            },

            {
                "period": "30d",
                "range": "2026-07-01,2026-08-09",
            },

        ]

        for params in parameter_sets:

            print()
            print("PARAMETER:")
            print(params)

            try:

                result = await api.get(
                    f"/heatpumps/{WP_ID}"
                    "/diagrams/graph_system/",
                    params=params,
                )

                if isinstance(result, dict):

                    print(
                        f"API PERIOD: "
                        f"{result.get('period')}"
                    )

                    data = result.get(
                        "data",
                        []
                    )

                    if isinstance(data, list):

                        print(
                            f"PUNKTE: {len(data)}"
                        )

                        if data:

                            print("ERSTER:")
                            print(data[0])

                            print("LETZTER:")
                            print(data[-1])

            except Exception as err:

                print(
                    f"FEHLER: {err}"
                )


        # ====================================================
        # 6. PAGINATION / OFFSET
        # ====================================================

        print_separator(
            "6. PAGINATION / OFFSET TEST"
        )

        offset_values = [
            0,
            48,
            96,
            144,
            288,
            1000,
        ]

        for offset in offset_values:

            params = {
                "period": "30d",
                "offset": offset,
            }

            print()
            print(
                f"OFFSET: {offset}"
            )

            try:

                result = await api.get(
                    f"/heatpumps/{WP_ID}"
                    "/diagrams/graph_system/",
                    params=params,
                )

                if isinstance(result, dict):

                    data = result.get(
                        "data",
                        []
                    )

                    print(
                        f"PUNKTE: "
                        f"{len(data) if isinstance(data, list) else '???'}"
                    )

                    if (
                        isinstance(data, list)
                        and data
                    ):

                        print("ERSTER:")
                        print(data[0])

                        print("LETZTER:")
                        print(data[-1])

            except Exception as err:

                print(
                    f"FEHLER: {err}"
                )


        # ====================================================
        # 7. LIMIT / OFFSET
        # ====================================================

        print_separator(
            "7. LIMIT / OFFSET TEST"
        )

        combinations = [

            {
                "period": "30d",
                "limit": 48,
            },

            {
                "period": "30d",
                "limit": 1000,
            },

            {
                "period": "30d",
                "limit": 48,
                "offset": 48,
            },

            {
                "period": "30d",
                "limit": 1000,
                "offset": 48,
            },

            {
                "period": "30d",
                "limit": 1000,
                "offset": 96,
            },

        ]

        for params in combinations:

            print()
            print("PARAMETER:")
            print(params)

            try:

                result = await api.get(
                    f"/heatpumps/{WP_ID}"
                    "/diagrams/graph_system/",
                    params=params,
                )

                if isinstance(result, dict):

                    data = result.get(
                        "data",
                        []
                    )

                    print(
                        f"PUNKTE: "
                        f"{len(data) if isinstance(data, list) else '???'}"
                    )

                    if (
                        isinstance(data, list)
                        and data
                    ):

                        print("ERSTER:")
                        print(data[0])

                        print("LETZTER:")
                        print(data[-1])

            except Exception as err:

                print(
                    f"FEHLER: {err}"
                )


        # ====================================================
        # 8. LOGS
        # ====================================================

        print_separator(
            "8. LOGS TEST"
        )

        try:

            result = await api.get(
                f"/heatpumps/{WP_ID}/logs/"
            )

            print_log_summary(
                result
            )

        except Exception as err:

            print()
            print("FEHLER:")
            print(repr(err))


        # ====================================================
        # 9. LOGS PAGINATION
        # ====================================================

        print_separator(
            "9. LOGS PAGINATION"
        )

        log_parameters = [

            {
                "limit": 20,
                "offset": 0,
            },

            {
                "limit": 20,
                "offset": 20,
            },

            {
                "limit": 20,
                "offset": 40,
            },

            {
                "limit": 50,
                "offset": 0,
            },

            {
                "limit": 100,
                "offset": 0,
            },

        ]

        for params in log_parameters:

            print()
            print("LOG PARAMETER:")
            print(params)

            try:

                result = await api.get(
                    f"/heatpumps/{WP_ID}/logs/",
                    params=params,
                )

                print_log_summary(
                    result
                )

            except Exception as err:

                print()
                print("FEHLER:")
                print(repr(err))


        # ====================================================
        # 10. LOGS EINTRÄGE DETAILLIERT
        # ====================================================

        print_separator(
            "10. LOG EINTRÄGE DETAILLIERT"
        )

        try:

            result = await api.get(
                f"/heatpumps/{WP_ID}/logs/",
                params={
                    "limit": 20,
                    "offset": 0,
                },
            )

            if isinstance(result, dict):

                results = result.get(
                    "results",
                    []
                )

                print()
                print(
                    f"Anzahl geladener Logeinträge: "
                    f"{len(results) if isinstance(results, list) else '???'}"
                )

                if isinstance(results, list):

                    for number, entry in enumerate(
                        results,
                        start=1,
                    ):

                        print()
                        print(
                            "-" * 100
                        )

                        print(
                            f"LOG #{number}"
                        )

                        print(
                            "-" * 100
                        )

                        if isinstance(entry, dict):

                            for key, value in entry.items():

                                print(
                                    f"{key}: {value!r}"
                                )

                        else:

                            print(entry)

        except Exception as err:

            print()
            print("FEHLER:")
            print(repr(err))


# ============================================================
# PROGRAMMSTART
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())