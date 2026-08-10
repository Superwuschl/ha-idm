import requests
from datetime import datetime


# ============================================================
# iDM API TEST – PERIODENVERHALTEN
# ============================================================

ACCESS_TOKEN = "OmuGrETkbh9TANzpvY1POv2vDt9kr6"
WP_ID = 3419

BASE_URL = "https://a.myidm.at/api/v1"

GRAPH = "graph_system"

PERIODS = [
    "1d",
    "3d",
    "7d",
    "14d",
    "30d",
    "1m",
    "3m",
    "6m",
    "1y",
]


# ============================================================
# API REQUEST
# ============================================================

def get_api(endpoint, params=None):

    url = BASE_URL + endpoint

    headers = {
        "Authorization": f"Access-Token {ACCESS_TOKEN}",
        "Accept": "application/json",
    }

    print()
    print("=" * 100)
    print("REQUEST")
    print("=" * 100)
    print("URL:", url)

    if params:
        print("PARAMETER:", params)

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )

    except Exception as e:

        print("REQUEST FEHLER:")
        print(repr(e))
        return None

    print("HTTP STATUS:", response.status_code)
    print("CONTENT-TYPE:", response.headers.get("Content-Type"))

    if response.status_code != 200:

        print("ANTWORT:")

        try:
            print(response.json())
        except Exception:
            print(response.text)

        return None

    try:
        return response.json()

    except Exception as e:

        print("JSON FEHLER:")
        print(repr(e))
        print(response.text)

        return None


# ============================================================
# PERIODEN AUSWERTEN
# ============================================================

def analyze_period(period):

    endpoint = (
        f"/heatpumps/{WP_ID}/diagrams/"
        f"{GRAPH}/"
    )

    data = get_api(
        endpoint,
        params={
            "period": period
        },
    )

    if not isinstance(data, dict):

        print()
        print(period, "-> KEINE GÜLTIGE ANTWORT")
        return

    print()
    print("-" * 100)
    print("PERIOD:", period)
    print("-" * 100)

    print("ROOT KEYS:")
    print(list(data.keys()))

    api_period = data.get("period")
    points = data.get("data")

    print()
    print("API PERIOD:", api_period)

    if not isinstance(points, list):

        print("DATA: KEINE LISTE")
        return

    print("PUNKTE:", len(points))

    if not points:

        print("KEINE DATEN")
        return

    first = points[0]
    last = points[-1]

    print()
    print("ERSTER DATENSATZ:")
    print(first)

    print()
    print("LETZTER DATENSATZ:")
    print(last)

    first_datetime = first.get("datetime")
    last_datetime = last.get("datetime")

    first_timestamp = first.get("timestamp")
    last_timestamp = last.get("timestamp")

    print()
    print("VON:", first_datetime)
    print("BIS:", last_datetime)

    print("ERSTER UNIX:", first_timestamp)
    print("LETZTER UNIX:", last_timestamp)

    if (
        isinstance(first_timestamp, (int, float))
        and isinstance(last_timestamp, (int, float))
    ):

        duration_hours = (
            last_timestamp - first_timestamp
        ) / 3600

        print(
            "DAUER h:",
            round(duration_hours, 2)
        )

    print()
    print("CHANNELS:")

    channels = data.get("channels")

    if isinstance(channels, list):

        print(channels)

    else:

        print("Keine Channel-Liste")

    print()
    print("CHANNEL LABELS:")

    labels = data.get("channel_labels")

    if isinstance(labels, dict):

        for channel_id, label in labels.items():

            print(
                f"  {channel_id}: {label}"
            )

    else:

        print("Keine Channel-Labels")


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():

    print()
    print("=" * 100)
    print("iDM PERIOD TEST")
    print("=" * 100)

    print()
    print("Wärmepumpe:", WP_ID)
    print("API:", BASE_URL)
    print("GRAPH:", GRAPH)

    print()
    print("=" * 100)
    print("PERIODEN-VERGLEICH")
    print("=" * 100)

    for period in PERIODS:

        analyze_period(period)

    print()
    print("=" * 100)
    print("TEST ABGESCHLOSSEN")
    print("=" * 100)


if __name__ == "__main__":
    main()