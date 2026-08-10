from __future__ import annotations

from pathlib import Path
import sys
import asyncio
import importlib.util
import aiohttp
from datetime import datetime


# ============================================================
# PFADE
# ============================================================

TEST_FILE = Path(__file__).resolve()

# ...\ha-idm\custom_components
BASE_DIR = TEST_FILE.parent.parent

# ...\ha-idm\custom_components\idm
IDM_DIR = BASE_DIR / "idm"

# ...\ha-idm\custom_components\idm\api.py
API_FILE = IDM_DIR / "api.py"


# ============================================================
# KONFIGURATION
# ============================================================

ACCESS_TOKEN = "Ria3MXnwpXvz9Z00vv4KWpNDwzctjV"

REFRESH_TOKEN = "vBEvzwARo1MBVztu652AdsBchpS2C2"

WP_ID = 3419

DIAGRAM = "graph_heat_a"


# ============================================================
# TEST-PERIODEN
# ============================================================

PERIODS = [
    "1d",
    "2d",
    "3d",
    "4d",
    "5d",
    "6d",
    "7d",
    "8d",
    "9d",
    "10d",
    "14d",
    "21d",
    "30d",
    "60d",
    "90d",
    "180d",
    "365d",
]


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def format_duration(seconds: float) -> str:

    hours = seconds / 3600

    if hours < 24:
        return f"{hours:.2f} h"

    return f"{hours / 24:.2f} d"


def get_grid_minutes(data: list[dict]) -> float | None:

    if len(data) < 2:
        return None

    timestamps = []

    for point in data:

        timestamp = point.get("timestamp")

        if timestamp is not None:
            timestamps.append(timestamp)

    if len(timestamps) < 2:
        return None

    intervals = []

    for index in range(1, len(timestamps)):

        delta = timestamps[index] - timestamps[index - 1]

        if delta > 0:
            intervals.append(delta)

    if not intervals:
        return None

    # häufigstes Intervall
    counts = {}

    for interval in intervals:
        counts[interval] = counts.get(interval, 0) + 1

    most_common = max(
        counts,
        key=counts.get,
    )

    return most_common / 60


# ============================================================
# API-DATEI PRÜFEN
# ============================================================

print()

print("=" * 80)
print("iDM PERIODEN-TEST")
print("=" * 80)

print()

print("API-Datei:")
print(API_FILE)


if not API_FILE.exists():

    print()

    print("FEHLER: api.py wurde nicht gefunden!")

    print()

    print("Erwarteter Pfad:")
    print(API_FILE)

    sys.exit(1)


print()

print("api.py gefunden.")


# ============================================================
# API-MODUL LADEN
# ============================================================

spec = importlib.util.spec_from_file_location(
    "idm_api",
    API_FILE,
)


if spec is None or spec.loader is None:

    print()

    print("FEHLER: API-Modul konnte nicht geladen werden!")

    sys.exit(1)


api_module = importlib.util.module_from_spec(spec)

sys.modules["idm_api"] = api_module

spec.loader.exec_module(api_module)


# ============================================================
# IDMApi
# ============================================================

IDMApi = api_module.IDMApi


# ============================================================
# TEST
# ============================================================

async def test_period(
    api: IDMApi,
    period: str,
) -> dict:

    try:

        result = await api.get_heat_a_diagram(period)

        if not isinstance(result, dict):

            return {
                "period": period,
                "error": "API liefert kein Dictionary",
            }

        data = result.get("data", [])

        delivered_period = result.get(
            "period",
            "",
        )

        if not data:

            return {
                "period": period,
                "delivered": delivered_period,
                "points": 0,
                "error": "Keine Daten",
            }

        first = data[0]

        last = data[-1]

        first_datetime = first.get("datetime")

        last_datetime = last.get("datetime")

        duration_seconds = None

        if first_datetime and last_datetime:

            dt0 = parse_datetime(first_datetime)

            dt1 = parse_datetime(last_datetime)

            duration_seconds = (
                dt1 - dt0
            ).total_seconds()

        grid_minutes = get_grid_minutes(data)

        return {
            "period": period,
            "delivered": delivered_period,
            "points": len(data),
            "first": first_datetime,
            "last": last_datetime,
            "duration": duration_seconds,
            "grid": grid_minutes,
            "error": None,
        }

    except Exception as err:

        return {
            "period": period,
            "error": (
                f"{type(err).__name__}: {err}"
            ),
        }


# ============================================================
# MAIN
# ============================================================

async def main():

    timeout = aiohttp.ClientTimeout(
        total=30
    )

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:

        api = IDMApi(
            session,
            ACCESS_TOKEN,
            REFRESH_TOKEN,
            WP_ID,
        )

        print()

        print("=" * 80)
        print("ERGEBNIS")
        print("=" * 80)

        print()

        print(
            f"{'Period':<8}"
            f"{'Geliefert':<10}"
            f"{'Punkte':>8}"
            f"{'Raster':>12}"
            f"{'Dauer':>12}"
            f"  Von"
            f"  Bis"
        )

        print("-" * 80)

        for period in PERIODS:

            result = await test_period(
                api,
                period,
            )

            if result.get("error"):

                print(
                    f"{period:<8}"
                    f"{result.get('delivered', ''):<10}"
                    f"{result.get('points', ''):>8}"
                    f"{'':>12}"
                    f"{'':>12}"
                    f"  FEHLER: "
                    f"{result['error']}"
                )

                continue

            grid = result["grid"]

            if grid is None:
                grid_text = "-"
            else:
                grid_text = f"{grid:.0f} min"

            duration = result["duration"]

            if duration is None:
                duration_text = "-"
            else:
                duration_text = format_duration(
                    duration
                )

            print(
                f"{result['period']:<8}"
                f"{result['delivered']:<10}"
                f"{result['points']:>8}"
                f"{grid_text:>12}"
                f"{duration_text:>12}"
                f"  {result['first']}"
                f"  {result['last']}"
            )

        print()

        print("=" * 80)
        print("TEST BEENDET")
        print("=" * 80)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())