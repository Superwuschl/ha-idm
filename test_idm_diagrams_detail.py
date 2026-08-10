import requests
import json


# ============================================================
# iDM DIAGRAM DETAILS
# ============================================================

ACCESS_TOKEN = "OmuGrETkbh9TANzpvY1POv2vDt9kr6"
WP_ID = 3419

BASE_URL = "https://a.myidm.at/api/v1"


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
            print(
                json.dumps(
                    response.json(),
                    indent=2,
                    ensure_ascii=False,
                )
            )
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
# REKURSIVE STRUKTURANALYSE
# ============================================================

def inspect_structure(value, path="ROOT", depth=0):

    indent = "  " * depth

    if depth > 6:
        print(
            indent +
            f"{path}: <MAX DEPTH>"
        )
        return

    if isinstance(value, dict):

        print(
            indent +
            f"{path}: dict "
            f"({len(value)} keys)"
        )

        for key, child in value.items():

            child_path = f"{path}.{key}"

            if isinstance(child, (dict, list)):

                inspect_structure(
                    child,
                    child_path,
                    depth + 1,
                )

            else:

                print(
                    indent +
                    f"  {key}: "
                    f"{type(child).__name__} = "
                    f"{repr(child)}"
                )

    elif isinstance(value, list):

        print(
            indent +
            f"{path}: list "
            f"({len(value)} items)"
        )

        for index, child in enumerate(value[:10]):

            child_path = (
                f"{path}[{index}]"
            )

            if isinstance(child, (dict, list)):

                inspect_structure(
                    child,
                    child_path,
                    depth + 1,
                )

            else:

                print(
                    indent +
                    f"  [{index}]: "
                    f"{type(child).__name__} = "
                    f"{repr(child)}"
                )

        if len(value) > 10:

            print(
                indent +
                f"  ... "
                f"{len(value) - 10} weitere"
            )

    else:

        print(
            indent +
            f"{path}: "
            f"{type(value).__name__} = "
            f"{repr(value)}"
        )


# ============================================================
# DIAGRAMS ROOT
# ============================================================

def test_diagrams_root():

    print()
    print("#" * 100)
    print("1. DIAGRAMS ROOT")
    print("#" * 100)

    endpoint = (
        f"/heatpumps/{WP_ID}/diagrams/"
    )

    data = get_api(endpoint)

    if data is None:
        return

    print()
    print("VOLLSTÄNDIGE ANTWORT:")
    print(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print("#" * 100)
    print("STRUKTURANALYSE")
    print("#" * 100)

    inspect_structure(data)


# ============================================================
# GRAPH ENDPOINTS
# ============================================================

def test_graph(graph_name):

    print()
    print("#" * 100)
    print("GRAPH:", graph_name)
    print("#" * 100)

    endpoint = (
        f"/heatpumps/{WP_ID}/diagrams/"
        f"{graph_name}/"
    )

    data = get_api(
        endpoint,
        params={
            "period": "7d"
        },
    )

    if data is None:
        return

    print()
    print("ROOT KEYS:")

    if isinstance(data, dict):
        print(list(data.keys()))

    print()
    print("STRUKTUR:")

    inspect_structure(data)


# ============================================================
# PARAMETER-TEST
# ============================================================

def test_parameters(graph_name):

    print()
    print("#" * 100)
    print("PARAMETER-TEST:", graph_name)
    print("#" * 100)

    endpoint = (
        f"/heatpumps/{WP_ID}/diagrams/"
        f"{graph_name}/"
    )

    parameters = [

        {},

        {
            "period": "7d",
        },

        {
            "period": "14d",
        },

        {
            "period": "30d",
        },

        {
            "period": "1y",
        },

        {
            "period": "7d",
            "limit": 1000,
        },

        {
            "period": "30d",
            "limit": 1000,
        },

        {
            "period": "1y",
            "limit": 1000,
        },

        {
            "period": "30d",
            "offset": 0,
        },

        {
            "period": "30d",
            "start": "2026-07-01",
        },

        {
            "period": "30d",
            "from": "2026-07-01",
        },

        {
            "period": "30d",
            "date": "2026-07-01",
        },

    ]

    for params in parameters:

        data = get_api(
            endpoint,
            params=params,
        )

        if not isinstance(data, dict):

            continue

        points = data.get("data")

        print()
        print("-" * 100)
        print(
            "PARAMETER:",
            params
        )

        print(
            "API PERIOD:",
            data.get("period")
        )

        if isinstance(points, list):

            print(
                "PUNKTE:",
                len(points)
            )

            if points:

                print(
                    "VON:",
                    points[0].get("datetime")
                )

                print(
                    "BIS:",
                    points[-1].get("datetime")
                )

        else:

            print(
                "DATA:",
                type(points).__name__
            )


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():

    print()
    print("=" * 100)
    print("iDM DIAGRAM DETAIL TEST")
    print("=" * 100)

    print()
    print("Wärmepumpe:", WP_ID)
    print("API:", BASE_URL)

    # --------------------------------------------------------
    # 1. diagrams root
    # --------------------------------------------------------

    test_diagrams_root()

    # --------------------------------------------------------
    # 2. bekannte Graphen
    # --------------------------------------------------------

    graphs = [
        "graph_system",
        "graph_heat_a",
        "graph_heat_b",
    ]

    for graph in graphs:

        test_graph(graph)

    # --------------------------------------------------------
    # 3. Parameter untersuchen
    # --------------------------------------------------------

    for graph in graphs:

        test_parameters(graph)

    print()
    print("=" * 100)
    print("DIAGNOSE ABGESCHLOSSEN")
    print("=" * 100)


if __name__ == "__main__":
    main()