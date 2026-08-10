import sys
import json
from pathlib import Path


# ============================================================
# iDM HISTORY / DIAGRAM ENDPOINT TEST
# ============================================================

print("=" * 100)
print("iDM HISTORY / DIAGRAM ENDPOINT TEST")
print("=" * 100)


# ============================================================
# PFADE
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
IDM_DIR = PROJECT_DIR / "custom_components" / "idm"

sys.path.insert(0, str(IDM_DIR))


# ============================================================
# KONFIGURATION
# ============================================================

WP_ID = 3419

BASE_URL = "https://a.myidm.at/api/v1"

ACCESS_TOKEN = "OmuGrETkbh9TANzpvY1POv2vDt9kr6"


# ============================================================
# API IMPORT
# ============================================================

try:
    from api import get_api

    print()
    print("API IMPORT: OK")
    print("API PFAD:")
    print(IDM_DIR / "api.py")

except Exception as e:

    print()
    print("FEHLER BEIM IMPORT VON api.py")
    print(type(e).__name__)
    print(str(e))
    sys.exit(1)


# ============================================================
# HILFSFUNKTION
# ============================================================

def request(name, endpoint, params=None):

    print()
    print("=" * 100)
    print(name)
    print("=" * 100)

    print("ENDPOINT:")
    print(endpoint)

    print("PARAMETER:")
    print(params)

    try:

        if params is None:
            result = get_api(
                ACCESS_TOKEN,
                endpoint,
            )
        else:
            result = get_api(
                ACCESS_TOKEN,
                endpoint,
                params=params,
            )

        print()
        print("ERGEBNIS-TYP:")
        print(type(result).__name__)

        if isinstance(result, dict):

            print()
            print("ROOT KEYS:")
            print(list(result.keys()))

            print()
            print("ANTWORT:")

            print(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False,
                )[:12000]
            )

        elif isinstance(result, list):

            print()
            print("LISTE:")

            print(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False,
                )[:12000]
            )

        else:

            print()
            print("WERT:")
            print(result)

        return result

    except Exception as e:

        print()
        print("FEHLER:")
        print(type(e).__name__)
        print(str(e))

        return None


# ============================================================
# 1. HEATPUMP ROOT
# ============================================================

request(
    "1. HEATPUMP ROOT",
    f"/heatpumps/{WP_ID}/",
)


# ============================================================
# 2. HEATPUMP HISTORY
# ============================================================

request(
    "2. HEATPUMP HISTORY",
    f"/heatpumps/{WP_ID}/history/",
)


# ============================================================
# 3. HEATPUMP STATISTICS
# ============================================================

request(
    "3. HEATPUMP STATISTICS",
    f"/heatpumps/{WP_ID}/statistics/",
)


# ============================================================
# 4. HEATPUMP DATA
# ============================================================

request(
    "4. HEATPUMP DATA",
    f"/heatpumps/{WP_ID}/data/",
)


# ============================================================
# 5. HEATPUMP VALUES
# ============================================================

request(
    "5. HEATPUMP VALUES",
    f"/heatpumps/{WP_ID}/values/",
)


# ============================================================
# 6. HEATPUMP MEASUREMENTS
# ============================================================

request(
    "6. HEATPUMP MEASUREMENTS",
    f"/heatpumps/{WP_ID}/measurements/",
)


# ============================================================
# 7. HEATPUMP RECORDS
# ============================================================

request(
    "7. HEATPUMP RECORDS",
    f"/heatpumps/{WP_ID}/records/",
)


# ============================================================
# 8. HEATPUMP LOG
# ============================================================

request(
    "8. HEATPUMP LOG",
    f"/heatpumps/{WP_ID}/log/",
)


# ============================================================
# 9. DIAGRAMS HISTORY
# ============================================================

request(
    "9. DIAGRAMS HISTORY",
    f"/heatpumps/{WP_ID}/diagrams/history/",
)


# ============================================================
# 10. DIAGRAMS DATA
# ============================================================

request(
    "10. DIAGRAMS DATA",
    f"/heatpumps/{WP_ID}/diagrams/data/",
)


# ============================================================
# 11. DIAGRAMS STATISTICS
# ============================================================

request(
    "11. DIAGRAMS STATISTICS",
    f"/heatpumps/{WP_ID}/diagrams/statistics/",
)


# ============================================================
# 12. GRAPH SYSTEM HISTORY
# ============================================================

request(
    "12. GRAPH SYSTEM HISTORY",
    f"/heatpumps/{WP_ID}/diagrams/graph_system/history/",
)


# ============================================================
# 13. GRAPH SYSTEM DATA
# ============================================================

request(
    "13. GRAPH SYSTEM DATA",
    f"/heatpumps/{WP_ID}/diagrams/graph_system/data/",
)


# ============================================================
# 14. GRAPH SYSTEM STATISTICS
# ============================================================

request(
    "14. GRAPH SYSTEM STATISTICS",
    f"/heatpumps/{WP_ID}/diagrams/graph_system/statistics/",
)


# ============================================================
# 15. GRAPH SYSTEM 7d
# ============================================================

request(
    "15. GRAPH SYSTEM 7d",
    f"/heatpumps/{WP_ID}/diagrams/graph_system/",
    {
        "period": "7d",
    },
)


# ============================================================
# 16. GRAPH SYSTEM 7d + interval
# ============================================================

request(
    "16. GRAPH SYSTEM 7d + interval",
    f"/heatpumps/{WP_ID}/diagrams/graph_system/",
    {
        "period": "7d",
        "interval": "1h",
    },
)


# ============================================================
# 17. GRAPH SYSTEM 30d + interval
# ============================================================

request(
    "17. GRAPH SYSTEM 30d + interval",
    f"/heatpumps/{WP_ID}/diagrams/graph_system/",
    {
        "period": "30d",
        "interval": "1h",
    },
)


# ============================================================
# 18. GRAPH SYSTEM 30d + resolution
# ============================================================

request(
    "18. GRAPH SYSTEM 30d + resolution",
    f"/heatpumps/{WP_ID}/diagrams/graph_system/",
    {
        "period": "30d",
        "resolution": "1h",
    },
)


# ============================================================
# 19. GRAPH SYSTEM 30d + aggregation
# ============================================================

request(
    "19. GRAPH SYSTEM 30d + aggregation
",
    f"/heatpumps/{WP_ID}/diagrams/graph_system/",
    {
        "period": "30d",
        "aggregation": "hour",
    },
)


# ============================================================
# 20. GRAPH SYSTEM 30d + interval + limit
# ============================================================

request(
    "20. GRAPH SYSTEM 30d + interval + limit",
    f"/heatpumps/{WP_ID}/diagrams/graph_system/",
    {
        "period": "30d",
        "interval": "1h",
        "limit": 1000,
    },
)


# ============================================================
# ENDE
# ============================================================

print()
print("=" * 100)
print("TEST ABGESCHLOSSEN")
print("=" * 100)