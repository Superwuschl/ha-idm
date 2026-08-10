from __future__ import annotations

import re
import sys

print()
print("=" * 100)
print("iDM DIAGRAM DISCOVERY TEST")
print("=" * 100)
print()


# ============================================================
# KONFIGURATION
# ============================================================

WP_ID = 3419

BASE_URL = "https://a.myidm.at/api/v1"


# ============================================================
# API IMPORT
# ============================================================

try:
    import api

    print("api.py erfolgreich importiert")

except Exception as e:
    print("FEHLER BEIM IMPORT VON api.py")
    print(e)
    sys.exit(1)


# ============================================================
# ACCESS TOKEN AUS api.py HOLEN
# ============================================================

def load_access_token():
    """
    Sucht ACCESS_TOKEN in api.py.
    Unterstützt:
        ACCESS_TOKEN = "..."
        ACCESS_TOKEN = '...'
    """

    # 1. Direktes Modul-Attribut
    token = getattr(api, "ACCESS_TOKEN", None)

    if token:
        return token

    # 2. Datei direkt durchsuchen
    try:
        with open(api.__file__, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.search(
            r'ACCESS_TOKEN\s*=\s*["\']([^"\']+)["\']',
            content,
        )

        if match:
            return match.group(1)

    except Exception as e:
        print("Fehler beim Lesen von api.py:")
        print(e)

    raise RuntimeError(
        "ACCESS_TOKEN wurde in api.py nicht gefunden."
    )


try:
    ACCESS_TOKEN = load_access_token()

except Exception as e:
    print()
    print("FEHLER:")
    print(e)
    print()
    print("Bitte prüfen, ob in api.py z.B. folgendes steht:")
    print()
    print('ACCESS_TOKEN = "DEIN_TOKEN"')
    print()
    sys.exit(1)


# ============================================================
# API FUNKTION
# ============================================================

def get_api(endpoint, params=None):

    try:
        result = api.get_api(
            ACCESS_TOKEN,
            endpoint,
            params=params,
        )

        return result

    except TypeError:

        # Falls deine get_api-Funktion keine params unterstützt
        if params:
            raise

        return api.get_api(
            ACCESS_TOKEN,
            endpoint,
        )


# ============================================================
# AUSGABE
# ============================================================

def print_result(result):

    if isinstance(result, dict):

        print(f"dict ({len(result)} keys)")

        for key, value in result.items():

            if isinstance(value, dict):
                print(
                    f"  {key}: dict ({len(value)} keys)"
                )

            elif isinstance(value, list):
                print(
                    f"  {key}: list ({len(value)} items)"
                )

            else:
                value_type = type(value).__name__

                text = repr(value)

                if len(text) > 200:
                    text = text[:200] + "..."

                print(
                    f"  {key}: {value_type} = {text}"
                )

    elif isinstance(result, list):

        print(
            f"list ({len(result)} items)"
        )

        if result:
            print(
                "erstes Element:"
            )
            print(
                repr(result[0])
            )

    else:

        print(
            f"{type(result).__name__}: {repr(result)}"
        )


# ============================================================
# REQUEST
# ============================================================

def request(name, endpoint, params=None):

    print()
    print("=" * 100)
    print(name)
    print("=" * 100)

    print()
    print("ENDPOINT:")
    print(endpoint)

    print()
    print("PARAMETER:")
    print(params)

    try:

        result = get_api(
            endpoint,
            params=params,
        )

        print()
        print("ERGEBNIS:")
        print_result(result)

        return result

    except Exception as e:

        print()
        print("FEHLER:")
        print(type(e).__name__)
        print(str(e))

        return None


# ============================================================
# 1. ROOT HEATPUMP
# ============================================================

request(
    "1. HEATPUMP ROOT",
    f"/heatpumps/{WP_ID}/",
)


# ============================================================
# 2. HEATPUMP OHNE SLASH
# ============================================================

request(
    "2. HEATPUMP OHNE TRAILING SLASH",
    f"/heatpumps/{WP_ID}",
)


# ============================================================
# 3. DIAGRAMS ROOT
# ============================================================

request(
    "3. DIAGRAMS ROOT",
    f"/heatpumps/{WP_ID}/diagrams/",
)


request(
    "4. DIAGRAMS ROOT OHNE SLASH",
    f"/heatpumps/{WP_ID}/diagrams",
)


# ============================================================
# 4. BEKANNTE FUNKTIONIERENDE DIAGRAMME
# ============================================================

diagram_names = [

    "graph_system",
    "system",
    "system_temperatures",
    "temperatures",
    "temperature",
    "graph",
    "graph_system_temperatures",

    "graph_heatpump",
    "graph_heating",
    "graph_energy",
    "graph_power",

    "energy",
    "power",
    "heating",
    "consumption",
    "production",

    "cop",
    "scop",

    "dhw",
    "hot_water",
    "warmwater",

    "heating_circuit",
    "heating_circuits",

    "heat_source",
    "heat_buffer",
    "cold_buffer",

    "solar",
    "solar_energy",

    "system_energy",
    "system_power",
]


# ============================================================
# 5. DIAGRAM NAMEN TESTEN
# ============================================================

print()
print()
print("=" * 100)
print("5. DIAGRAM NAMEN")
print("=" * 100)

successful_diagrams = []


for diagram_name in diagram_names:

    endpoint = (
        f"/heatpumps/{WP_ID}/"
        f"diagrams/{diagram_name}/"
    )

    print()
    print("-" * 100)
    print(
        f"TEST: {diagram_name}"
    )

    result = request(
        f"DIAGRAM: {diagram_name}",
        endpoint,
    )

    if result is not None:

        successful_diagrams.append(
            diagram_name
        )


# ============================================================
# 6. GRAPH_SYSTEM MIT VERSCHIEDENEN PERIODEN
# ============================================================

print()
print()
print("=" * 100)
print("6. GRAPH_SYSTEM PERIODEN")
print("=" * 100)


periods = [
    "1d",
    "2d",
    "7d",
    "14d",
    "30d",
    "60d",
    "90d",
    "180d",
    "365d",
]


for period in periods:

    request(
        f"GRAPH_SYSTEM PERIOD={period}",
        f"/heatpumps/{WP_ID}/diagrams/graph_system/",
        {
            "period": period,
        },
    )


# ============================================================
# 7. GRAPH_SYSTEM MIT PARAMETERN
# ============================================================

print()
print()
print("=" * 100)
print("7. GRAPH_SYSTEM PARAMETER-KOMBINATIONEN")
print("=" * 100)


parameter_tests = [

    {
        "period": "1d",
    },

    {
        "period": "7d",
    },

    {
        "period": "30d",
    },

    {
        "period": "30d",
        "days": 30,
    },

    {
        "period": "30d",
        "duration": 30,
    },

    {
        "period": "30d",
        "hours": 720,
    },

    {
        "period": "30d",
        "interval": 30,
    },

    {
        "period": "30d",
        "step": 30,
    },

    {
        "period": "30d",
        "points": 1000,
    },

    {
        "period": "30d",
        "count": 1000,
    },

    {
        "period": "30d",
        "start": "2026-07-01T00:00:00",
        "end": "2026-08-09T23:59:59",
    },

    {
        "period": "30d",
        "from": "2026-07-01T00:00:00",
        "to": "2026-08-09T23:59:59",
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

]


for params in parameter_tests:

    request(
        "GRAPH_SYSTEM PARAMETER TEST",
        f"/heatpumps/{WP_ID}/diagrams/graph_system/",
        params,
    )


# ============================================================
# 8. LOGS
# ============================================================

request(
    "8. LOGS",
    f"/heatpumps/{WP_ID}/logs/",
)


# ============================================================
# 9. LOGS MIT LIMIT / OFFSET
# ============================================================

request(
    "9. LOGS LIMIT 100",
    f"/heatpumps/{WP_ID}/logs/",
    {
        "limit": 100,
    },
)


request(
    "10. LOGS OFFSET 20",
    f"/heatpumps/{WP_ID}/logs/",
    {
        "limit": 20,
        "offset": 20,
    },
)


# ============================================================
# 10. API INFORMATION
# ============================================================

request(
    "11. API ROOT",
    "/",
)


request(
    "12. API HEATPUMPS",
    "/heatpumps/",
)


# ============================================================
# ZUSAMMENFASSUNG
# ============================================================

print()
print()
print("=" * 100)
print("DISCOVERY ABGESCHLOSSEN")
print("=" * 100)

print()
print("Erfolgreich getestete Diagramm-Namen:")

if successful_diagrams:

    for name in successful_diagrams:
        print(
            f"  + {name}"
        )

else:

    print(
        "  Keine zusätzlichen Diagramme gefunden."
    )


print()
print("=" * 100)
print("ENDE")
print("=" * 100)