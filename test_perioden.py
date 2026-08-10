import asyncio
import importlib.util
from datetime import datetime, timezone
from pprint import pprint

# ============================================================
# API-Datei direkt laden
#
# Verhindert Import von custom_components.idm.__init__
# ============================================================

API_FILE = (
    r"C:\Users\Bernd\documents\ha-idm"
    r"\custom_components\idm\api.py"
)

spec = importlib.util.spec_from_file_location(
    "idm_api",
    API_FILE,
)

idm_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(idm_api)

IDMApi = idm_api.IDMApi


# ============================================================
# Zugangsdaten
# ============================================================

ACCESS_TOKEN = "Ria3MXnwpXvz9Z00vv4KWpNDwzctjV"
REFRESH_TOKEN = "vBEvzwARo1MBVztu652AdsBchpS2C2"

WP_ID = 3419


# ============================================================
# Zu testende Perioden
# ============================================================

PERIODEN = [
    "1d",
    "2d",
    "3d",
    "4d",
    "5d",
    "6d",
    "7d",
    "8d",
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
# Hilfsfunktion
# ============================================================

def format_timestamp(timestamp):

    if timestamp is None:
        return "?"

    try:
        dt = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )

        return dt.isoformat()

    except Exception:
        return str(timestamp)


# ============================================================
# Zeitinformationen aus DATA bestimmen
# ============================================================

def analyse_data(data):

    if not isinstance(data, list):
        return {
            "points": 0,
            "timestamps": [],
            "raster": None,
            "raster_unique": [],
            "duration_hours": None,
        }

    timestamps = []

    for point in data:

        if not isinstance(point, dict):
            continue

        timestamp = point.get("timestamp")

        if timestamp is not None:
            timestamps.append(timestamp)

    # --------------------------------------------------------
    # Raster
    # --------------------------------------------------------

    rasterwerte = []

    for i in range(1, len(timestamps)):

        delta = (
            timestamps[i]
            - timestamps[i - 1]
        )

        rasterwerte.append(delta)

    raster_unique = sorted(
        set(rasterwerte)
    )

    raster = (
        rasterwerte[0]
        if rasterwerte
        else None
    )

    # --------------------------------------------------------
    # Dauer
    # --------------------------------------------------------

    if len(timestamps) >= 2:

        duration_seconds = (
            timestamps[-1]
            - timestamps[0]
        )

        duration_hours = (
            duration_seconds / 3600
        )

    else:

        duration_hours = None

    return {
        "points": len(data),
        "timestamps": timestamps,
        "raster": raster,
        "raster_unique": raster_unique,
        "duration_hours": duration_hours,
    }


# ============================================================
# Haupttest
# ============================================================

async def main():

    import aiohttp

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

        print()
        print("=" * 120)
        print("iDM GRAPH_HEAT_A – VOLLSTÄNDIGE API-ANALYSE")
        print("=" * 120)
        print()

        ergebnisse = []

        # ====================================================
        # TEST
        # ====================================================

        for period in PERIODEN:

            print()
            print("#" * 120)
            print(f"TEST: {period}")
            print("#" * 120)
            print()

            try:

                result = await api.get_heat_a_diagram(
                    period=period
                )

                # =================================================
                # API-RESPONSE
                # =================================================

                print("API RESPONSE TYP:")
                print(type(result))

                print()
                print("API RESPONSE KEYS:")
                print(list(result.keys()))

                # =================================================
                # METADATEN
                # =================================================

                print()
                print("-" * 80)
                print("META-DATEN")
                print("-" * 80)

                print(
                    "diagram:",
                    result.get("diagram")
                )

                print(
                    "period:",
                    result.get("period")
                )

                print(
                    "channels:",
                    result.get("channels")
                )

                print(
                    "channel_labels:"
                )

                pprint(
                    result.get("channel_labels"),
                    sort_dicts=False
                )

                # =================================================
                # DATA
                # =================================================

                data = result.get(
                    "data"
                )

                print()
                print("-" * 80)
                print("DATA")
                print("-" * 80)

                print(
                    "data type:",
                    type(data)
                )

                if not isinstance(data, list):

                    print(
                        "FEHLER: data ist keine Liste"
                    )

                    ergebnisse.append({
                        "period": period,
                        "returned_period": result.get(
                            "period"
                        ),
                        "points": 0,
                        "error": "data ist keine Liste",
                    })

                    continue

                print(
                    "Datenpunkte:",
                    len(data)
                )

                # =================================================
                # Analyse
                # =================================================

                analyse = analyse_data(
                    data
                )

                points = analyse[
                    "points"
                ]

                raster = analyse[
                    "raster"
                ]

                raster_unique = analyse[
                    "raster_unique"
                ]

                duration_hours = analyse[
                    "duration_hours"
                ]

                # =================================================
                # ZEITRAUM
                # =================================================

                print()
                print("-" * 80)
                print("ZEITRAUM")
                print("-" * 80)

                if data:

                    first = data[0]
                    last = data[-1]

                    first_timestamp = first.get(
                        "timestamp"
                    )

                    last_timestamp = last.get(
                        "timestamp"
                    )

                    first_datetime = first.get(
                        "datetime"
                    )

                    last_datetime = last.get(
                        "datetime"
                    )

                    print(
                        "Erster Timestamp:",
                        first_timestamp
                    )

                    print(
                        "Erster Timestamp UTC:",
                        format_timestamp(
                            first_timestamp
                        )
                    )

                    print(
                        "Erstes datetime:",
                        first_datetime
                    )

                    print()

                    print(
                        "Letzter Timestamp:",
                        last_timestamp
                    )

                    print(
                        "Letzter Timestamp UTC:",
                        format_timestamp(
                            last_timestamp
                        )
                    )

                    print(
                        "Letztes datetime:",
                        last_datetime
                    )

                    print()

                    if duration_hours is not None:

                        print(
                            f"Dauer: "
                            f"{duration_hours:.2f} Stunden"
                        )

                        print(
                            f"Dauer: "
                            f"{duration_hours / 24:.2f} Tage"
                        )

                else:

                    first = None
                    last = None

                    print(
                        "KEINE DATEN"
                    )

                # =================================================
                # RASTER
                # =================================================

                print()
                print("-" * 80)
                print("RASTER")
                print("-" * 80)

                print(
                    "Raster:",
                    f"{raster}s"
                    if raster is not None
                    else "?"
                )

                print(
                    "Raster in Minuten:",
                    (
                        f"{raster / 60:.2f}"
                        if raster is not None
                        else "?"
                    )
                )

                print(
                    "Unterschiedliche Raster:",
                    raster_unique
                )

                print(
                    "Raster konstant:",
                    (
                        "JA"
                        if len(raster_unique) <= 1
                        else "NEIN"
                    )
                )

                # =================================================
                # ERSTE PUNKTE
                # =================================================

                print()
                print("-" * 80)
                print("ERSTE PUNKTE")
                print("-" * 80)

                for index, point in enumerate(
                    data[:5]
                ):

                    print()
                    print(
                        f"PUNKT {index}:"
                    )

                    pprint(
                        point,
                        sort_dicts=False
                    )

                # =================================================
                # LETZTE PUNKTE
                # =================================================

                print()
                print("-" * 80)
                print("LETZTE PUNKTE")
                print("-" * 80)

                start_index = max(
                    0,
                    len(data) - 5
                )

                for index in range(
                    start_index,
                    len(data)
                ):

                    print()
                    print(
                        f"PUNKT {index}:"
                    )

                    pprint(
                        data[index],
                        sort_dicts=False
                    )

                # =================================================
                # VOLLSTÄNDIGE RESPONSE
                # =================================================

                print()
                print("-" * 80)
                print("VOLLSTÄNDIGE API-RESPONSE")
                print("-" * 80)

                print()

                # Nur bei kleinen Antworten vollständig ausgeben.
                # Bei langen DATA-Listen würde die Ausgabe unnötig groß.
                response_copy = dict(result)
                response_copy["data"] = (
                    f"<{len(data)} Datenpunkte>"
                )

                pprint(
                    response_copy,
                    sort_dicts=False
                )

                # =================================================
                # ERGEBNIS SPEICHERN
                # =================================================

                ergebnisse.append({
                    "period": period,
                    "returned_period": result.get(
                        "period"
                    ),
                    "diagram": result.get(
                        "diagram"
                    ),
                    "points": points,
                    "raster": raster,
                    "raster_unique": raster_unique,
                    "duration_hours": duration_hours,
                    "first_timestamp": (
                        first.get("timestamp")
                        if first
                        else None
                    ),
                    "last_timestamp": (
                        last.get("timestamp")
                        if last
                        else None
                    ),
                    "first_datetime": (
                        first.get("datetime")
                        if first
                        else None
                    ),
                    "last_datetime": (
                        last.get("datetime")
                        if last
                        else None
                    ),
                })

            except Exception as err:

                print()
                print(
                    "FEHLER:"
                )

                print(
                    f"{type(err).__name__}: {err}"
                )

                ergebnisse.append({
                    "period": period,
                    "error": (
                        f"{type(err).__name__}: {err}"
                    ),
                })

        # ========================================================
        # ABSCHLUSSTABELLE
        # ========================================================

        print()
        print()
        print("=" * 120)
        print("ZUSAMMENFASSUNG")
        print("=" * 120)
        print()

        print(
            f"{'Period':<8}"
            f"{'Geliefert':<12}"
            f"{'Punkte':<9}"
            f"{'Raster':<12}"
            f"{'Dauer h':<12}"
            f"{'Dauer d':<12}"
            f"{'Von':<28}"
            f"{'Bis':<28}"
        )

        print("-" * 130)

        for item in ergebnisse:

            if "error" in item:

                print(
                    f"{item['period']:<8}"
                    f"FEHLER: {item['error']}"
                )

                continue

            duration_hours = item.get(
                "duration_hours"
            )

            duration_days = (
                duration_hours / 24
                if duration_hours is not None
                else None
            )

            raster = item.get(
                "raster"
            )

            print(
                f"{item['period']:<8}"
                f"{str(item.get('returned_period')):<12}"
                f"{item.get('points', 0):<9}"
                f"{str(raster) + 's':<12}"
                f"{duration_hours:.2f}"
                f"{'':<6}"
                f"{duration_days:.2f}"
                f"{'':<6}"
                f"{str(item.get('first_datetime')):<28}"
                f"{str(item.get('last_datetime')):<28}"
            )

        # ========================================================
        # SPEZIELLER VERGLEICH
        # ========================================================

        print()
        print()
        print("=" * 120)
        print("SPEZIELLER PERIODENVERGLEICH")
        print("=" * 120)
        print()

        for item in ergebnisse:

            if "error" in item:
                continue

            period = item["period"]
            returned = item.get(
                "returned_period"
            )
            points = item.get(
                "points"
            )
            duration = item.get(
                "duration_hours"
            )
            raster = item.get(
                "raster"
            )

            print(
                f"{period:>6} | "
                f"API={str(returned):<6} | "
                f"Punkte={points:<4} | "
                f"Raster={str(raster) + 's':<8} | "
                f"Dauer="
                f"{duration:.2f} h"
                if duration is not None
                else
                f"{period:>6} | "
                f"API={str(returned):<6} | "
                f"Punkte={points:<4} | "
                f"Raster={str(raster) + 's':<8} | "
                f"Dauer=?"
            )

        print()
        print("=" * 120)
        print("TEST ABGESCHLOSSEN")
        print("=" * 120)


# ============================================================
# Start
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())