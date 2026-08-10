import requests
import json
from urllib.parse import urljoin


# ============================================================
# KONFIGURATION
# ============================================================

BASE_URL = "https://a.myidm.at/api/v1/"
TOKEN = "Ria3MXnwpXvz9Z00vv4KWpNDwzctjV"
WP_ID = 3419

HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Accept": "application/json",
}


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def print_line():
    print("#" * 100)


def request_json(path, params=None):
    url = urljoin(BASE_URL, path.lstrip("/"))

    print()
    print_line()
    print("REQUEST")
    print_line()
    print("URL:", url)

    if params:
        print("PARAMETER:", params)

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20,
        )

        print("HTTP STATUS:", response.status_code)
        print("CONTENT-TYPE:", response.headers.get("content-type"))

        try:
            data = response.json()
        except Exception:
            print("ANTWORT IST KEIN JSON")
            print(response.text[:5000])
            return None

        if response.status_code != 200:
            print("ANTWORT:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return None

        return data

    except Exception as e:
        print("REQUEST FEHLER:")
        print(type(e).__name__, e)
        return None


def dump_object(name, obj):
    print()
    print_line()
    print(name)
    print_line()

    print("DATENTYP:")
    print(type(obj).__name__)

    if isinstance(obj, dict):
        print("KEYS:")
        print(list(obj.keys()))

    print()
    print("VOLLSTÄNDIGE ANTWORT:")
    print(json.dumps(obj, indent=2, ensure_ascii=False))


# ============================================================
# 1. HEATPUMP ROOT
# ============================================================

heatpump = request_json(
    f"/heatpumps/{WP_ID}/"
)

if heatpump:
    dump_object(
        "1. HEATPUMP ROOT – VOLLSTÄNDIG",
        heatpump,
    )

    print()
    print_line()
    print("RELEVANTE HEATPUMP-FELDER")
    print_line()

    for key in [
        "wp_id",
        "myidm_id",
        "name",
        "serialnumber",
        "wp_type",
        "logfreq",
        "online",
        "navpro",
        "navpro_online",
        "nav20",
        "nav20_online",
        "last_online",
        "nav_version",
        "navpro_version",
        "branch",
        "services",
        "loglength",
        "can_view_diagram",
        "editable_fields",
    ]:
        print(f"{key}:")
        print(json.dumps(
            heatpump.get(key),
            indent=2,
            ensure_ascii=False,
        ))


# ============================================================
# 2. DIAGRAMS ROOT – VOLLSTÄNDIG
# ============================================================

diagrams = request_json(
    f"/heatpumps/{WP_ID}/diagrams/"
)

if diagrams:
    dump_object(
        "2. DIAGRAMS ROOT – VOLLSTÄNDIG",
        diagrams,
    )


# ============================================================
# 3. DIAGRAMS ROOT ANALYSE
# ============================================================

if isinstance(diagrams, dict):

    print()
    print_line()
    print("3. DIAGRAMS ROOT – STRUKTURANALYSE")
    print_line()

    for key, value in diagrams.items():

        print()
        print("FELD:", key)
        print("DATENTYP:", type(value).__name__)

        if isinstance(value, list):

            print("ANZAHL:", len(value))

            for index, item in enumerate(value):

                print()
                print(f"ITEM {index}:")

                if isinstance(item, dict):
                    print("KEYS:", list(item.keys()))

                    for k, v in item.items():
                        print(
                            f"  {k}: "
                            + json.dumps(
                                v,
                                ensure_ascii=False,
                            )
                        )
                else:
                    print(
                        json.dumps(
                            item,
                            ensure_ascii=False,
                        )
                    )

        elif isinstance(value, dict):

            print(
                json.dumps(
                    value,
                    indent=2,
                    ensure_ascii=False,
                )
            )

        else:

            print(
                json.dumps(
                    value,
                    ensure_ascii=False,
                )
            )


# ============================================================
# 4. ALLE MÖGLICHEN DIAGRAMM-ENDPUNKTE
# ============================================================

print()
print_line()
print("4. DIAGRAMM-ENDPUNKTE AUS METADATEN")
print_line()

diagram_paths = []

if isinstance(diagrams, dict):

    def find_urls(obj, location="root"):

        if isinstance(obj, dict):

            for key, value in obj.items():

                if isinstance(value, str):

                    if (
                        "diagram" in value.lower()
                        or "graph_" in value.lower()
                        or "/heatpumps/" in value
                    ):
                        print(
                            f"{location}.{key}: {value}"
                        )

                        diagram_paths.append(value)

                else:
                    find_urls(
                        value,
                        f"{location}.{key}",
                    )

        elif isinstance(obj, list):

            for index, value in enumerate(obj):

                find_urls(
                    value,
                    f"{location}[{index}]",
                )

    find_urls(diagrams)


# ============================================================
# 5. BEKANNTE GRAPH-ENDPUNKTE
# ============================================================

known_graphs = [
    "graph_system",
    "graph_heat_a",
    "graph_heat_b",
]

print()
print_line()
print("5. BEKANNTE GRAPH-ENDPUNKTE")
print_line()

for graph in known_graphs:

    data = request_json(
        f"/heatpumps/{WP_ID}/diagrams/{graph}/",
        params={"period": "7d"},
    )

    if not isinstance(data, dict):
        continue

    print()
    print("GRAPH:", graph)

    print("ROOT KEYS:")
    print(list(data.keys()))

    channels = data.get("channels")
    labels = data.get("channel_labels")
    values = data.get("data")

    print()
    print("CHANNELS:")
    print(json.dumps(
        channels,
        indent=2,
        ensure_ascii=False,
    ))

    print()
    print("CHANNEL LABELS:")
    print(json.dumps(
        labels,
        indent=2,
        ensure_ascii=False,
    ))

    print()
    print("DATA-PUNKTE:")

    if isinstance(values, list):

        print("ANZAHL:", len(values))

        if values:
            print()
            print("ERSTER:")
            print(json.dumps(
                values[0],
                indent=2,
                ensure_ascii=False,
            ))

            print()
            print("LETZTER:")
            print(json.dumps(
                values[-1],
                indent=2,
                ensure_ascii=False,
            ))


# ============================================================
# 6. CHANNELS – GEZIELTE CHANNELS AUS DEN GRAPHEN
# ============================================================

channel_ids = [
    1,
    2,
    4,
    5,
    6,
    7,
    9,
    16,
    99,
    106,
    123,
    130,
]

print()
print_line()
print("6. CHANNEL-DEFINITIONEN")
print_line()

for channel_id in channel_ids:

    data = request_json(
        f"/channels/{channel_id}/"
    )

    if data is not None:

        print()
        print(f"CHANNEL {channel_id}")
        print(json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ))


# ============================================================
# 7. TOPICS – ALLE RELEVANTEN TOPICS
# ============================================================

topics = request_json(
    "/topics/",
    params={
        "limit": 100,
        "offset": 0,
    },
)

if isinstance(topics, dict):

    results = topics.get("results", [])

    print()
    print_line()
    print("7. TOPICS – RELEVANTE CHANNEL-ZUORDNUNG")
    print_line()

    interesting_channels = set(channel_ids)

    for topic in results:

        if not isinstance(topic, dict):
            continue

        topic_channels = set(
            topic.get("channel_ids", [])
        )

        overlap = (
            topic_channels
            & interesting_channels
        )

        if overlap:

            print()
            print("TOPIC:")
            print(
                topic.get("id"),
                topic.get("text_title"),
            )

            print(
                "TREFFER CHANNELS:",
                sorted(overlap),
            )

            print(
                "ALLE CHANNELS:",
                topic_channels,
            )


# ============================================================
# 8. DIAGRAM-PERIOD VERGLEICH
# ============================================================

print()
print_line()
print("8. PERIOD-VERGLEICH")
print_line()

periods = [
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

for graph in known_graphs:

    print()
    print("GRAPH:", graph)

    for period in periods:

        data = request_json(
            f"/heatpumps/{WP_ID}/diagrams/{graph}/",
            params={"period": period},
        )

        if not isinstance(data, dict):
            print(
                period,
                "-> KEINE GÜLTIGE ANTWORT"
            )
            continue

        values = data.get("data", [])

        if not isinstance(values, list):
            values = []

        timestamps = []

        for item in values:

            if isinstance(item, dict):
                ts = item.get("timestamp")

                if isinstance(ts, (int, float)):
                    timestamps.append(ts)

        print()
        print(
            f"{period:>5} | "
            f"Punkte={len(values):>4}",
            end=""
        )

        if len(timestamps) >= 2:

            duration_h = (
                timestamps[-1]
                - timestamps[0]
            ) / 3600

            print(
                f" | Dauer={duration_h:>8.2f} h"
            )

        else:

            print(
                " | Dauer=n/a"
            )


# ============================================================
# 9. ABSCHLUSS
# ============================================================

print()
print_line()
print("DIAGNOSE ABGESCHLOSSEN")
print_line()

print(
    """
WICHTIG:
Bitte die komplette Konsolenausgabe posten.

Besonders wichtig sind:

1. HEATPUMP ROOT – VOLLSTÄNDIG
2. DIAGRAMS ROOT – VOLLSTÄNDIG
3. DIAGRAMS ROOT – STRUKTURANALYSE
4. DIAGRAMM-ENDPUNKTE AUS METADATEN
5. CHANNEL-DEFINITIONEN
6. TOPICS
7. PERIOD-VERGLEICH

NICHTS aus der Ausgabe kürzen.
"""
)