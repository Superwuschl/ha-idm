import asyncio
import aiohttp
import json


# ==============================================================
# KONFIGURATION
# ==============================================================

ACCESS_TOKEN = "Ria3MXnwpXvz9Z00vv4KWpNDwzctjV"

WP_ID = 3419

BASE_URL = "https://a.myidm.at/api/v1"


# ==============================================================
# API GET
# ==============================================================

async def api_get(session, endpoint, params=None):

    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint

    url = BASE_URL + endpoint

    headers = {
        "Authorization": f"Access-Token {ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://www.myidm.at",
        "Referer": "https://www.myidm.at/",
        "User-Agent": "Mozilla/5.0",
    }

    print()
    print("=" * 100)
    print("REQUEST")
    print("=" * 100)
    print(url)

    if params:
        print("PARAMETER:")
        print(params)

    try:

        async with session.get(
            url,
            headers=headers,
            params=params,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:

            print()
            print("HTTP STATUS:", response.status)

            text = await response.text()

            print("CONTENT-TYPE:", response.headers.get("Content-Type"))

            if response.status != 200:

                print()
                print("ANTWORT:")
                print(text[:3000])

                return None

            try:
                result = json.loads(text)

            except json.JSONDecodeError:

                print()
                print("KEIN JSON:")
                print(text[:3000])

                return None

            return result

    except Exception as err:

        print()
        print("FEHLER:")
        print(type(err).__name__, err)

        return None


# ==============================================================
# AUSGABE
# ==============================================================

def print_result(name, result):

    print()
    print("#" * 100)
    print(name)
    print("#" * 100)

    if result is None:

        print("KEINE ANTWORT")

        return

    print()
    print("DATENTYP:")
    print(type(result).__name__)

    if isinstance(result, dict):

        print()
        print("ROOT KEYS:")
        print(list(result.keys()))

        # ------------------------------------------------------
        # Pagination
        # ------------------------------------------------------

        if "count" in result:
            print()
            print("COUNT:")
            print(result.get("count"))

        if "next" in result:
            print()
            print("NEXT:")
            print(result.get("next"))

        if "previous" in result:
            print()
            print("PREVIOUS:")
            print(result.get("previous"))

        # ------------------------------------------------------
        # Ergebnisse
        # ------------------------------------------------------

        if "results" in result:

            results = result.get("results")

            print()
            print("RESULTS DATENTYP:")
            print(type(results).__name__)

            if isinstance(results, list):

                print("RESULTS ANZAHL:")
                print(len(results))

                for index, item in enumerate(results[:10]):

                    print()
                    print(f"RESULT {index}:")

                    if isinstance(item, dict):

                        print(
                            json.dumps(
                                item,
                                indent=2,
                                ensure_ascii=False,
                            )[:5000]
                        )

                    else:

                        print(repr(item))

        # ------------------------------------------------------
        # Häufige Datenfelder
        # ------------------------------------------------------

        for key in (
            "data",
            "channels",
            "channel_labels",
            "values",
            "items",
            "topics",
            "parameters",
        ):

            if key in result:

                value = result[key]

                print()
                print(f"FELD {key}:")
                print("DATENTYP:", type(value).__name__)

                if isinstance(value, list):

                    print("ANZAHL:", len(value))

                    for item in value[:5]:

                        print(
                            json.dumps(
                                item,
                                indent=2,
                                ensure_ascii=False,
                            )
                            if isinstance(item, (dict, list))
                            else repr(item)
                        )

                elif isinstance(value, dict):

                    print(
                        json.dumps(
                            value,
                            indent=2,
                            ensure_ascii=False,
                        )[:5000]
                    )

                else:

                    print(repr(value))

    elif isinstance(result, list):

        print()
        print("LISTENLÄNGE:")
        print(len(result))

        for index, item in enumerate(result[:10]):

            print()
            print(f"ITEM {index}:")

            print(
                json.dumps(
                    item,
                    indent=2,
                    ensure_ascii=False,
                )
                if isinstance(item, (dict, list))
                else repr(item)
            )

    else:

        print()
        print(repr(result))


# ==============================================================
# HAUPTTEST
# ==============================================================

async def main():

    print()
    print("=" * 100)
    print("iDM API – RESOURCE / HISTORICAL DATA DIAGNOSE")
    print("=" * 100)

    print()
    print("Wärmepumpe:", WP_ID)
    print("API:", BASE_URL)

    async with aiohttp.ClientSession() as session:

        # ======================================================
        # 1. API ROOT
        # ======================================================

        result = await api_get(
            session,
            "/",
        )

        print_result(
            "1. API ROOT",
            result,
        )

        # ======================================================
        # 2. CHANNELS ROOT
        # ======================================================

        result = await api_get(
            session,
            "/channels/",
        )

        print_result(
            "2. CHANNELS ROOT",
            result,
        )

        # ======================================================
        # 3. CHANNELS MIT WP-ID
        # ======================================================

        result = await api_get(
            session,
            f"/channels/{WP_ID}/",
        )

        print_result(
            "3. CHANNELS / WP-ID",
            result,
        )

        # ======================================================
        # 4. DATA-ACT-CHANNELS ROOT
        # ======================================================

        result = await api_get(
            session,
            "/data-act-channels/",
        )

        print_result(
            "4. DATA-ACT-CHANNELS ROOT",
            result,
        )

        # ======================================================
        # 5. DATA-ACT-CHANNELS MIT WP-ID
        # ======================================================

        result = await api_get(
            session,
            f"/data-act-channels/{WP_ID}/",
        )

        print_result(
            "5. DATA-ACT-CHANNELS / WP-ID",
            result,
        )

        # ======================================================
        # 6. VIRTUAL CHANNELS
        # ======================================================

        result = await api_get(
            session,
            "/virtual-channels/",
        )

        print_result(
            "6. VIRTUAL-CHANNELS ROOT",
            result,
        )

        # ======================================================
        # 7. TOPICS
        # ======================================================

        result = await api_get(
            session,
            "/topics/",
        )

        print_result(
            "7. TOPICS ROOT",
            result,
        )

        # ======================================================
        # 8. PARAMETERS
        # ======================================================

        result = await api_get(
            session,
            "/parameters/",
        )

        print_result(
            "8. PARAMETERS ROOT",
            result,
        )

        # ======================================================
        # 9. PARAMETER MIT WP-ID
        # ======================================================

        result = await api_get(
            session,
            f"/parameters/{WP_ID}/",
        )

        print_result(
            "9. PARAMETERS / WP-ID",
            result,
        )

        # ======================================================
        # 10. AGGREGATED DEVICES
        # ======================================================

        result = await api_get(
            session,
            "/aggregated-devices/",
        )

        print_result(
            "10. AGGREGATED-DEVICES ROOT",
            result,
        )

        # ======================================================
        # 11. AGGREGATED DEVICES MIT WP-ID
        # ======================================================

        result = await api_get(
            session,
            f"/aggregated-devices/{WP_ID}/",
        )

        print_result(
            "11. AGGREGATED-DEVICES / WP-ID",
            result,
        )

        # ======================================================
        # 12. HEATPUMP ROOT
        # ======================================================

        result = await api_get(
            session,
            f"/heatpumps/{WP_ID}/",
        )

        print_result(
            "12. HEATPUMP ROOT",
            result,
        )

        # ======================================================
        # 13. DIAGRAMS ROOT
        # ======================================================

        result = await api_get(
            session,
            f"/heatpumps/{WP_ID}/diagrams/",
        )

        print_result(
            "13. DIAGRAMS ROOT",
            result,
        )

        # ======================================================
        # 14. GRAPH SYSTEM 7d
        # ======================================================

        result = await api_get(
            session,
            f"/heatpumps/{WP_ID}/diagrams/graph_system/",
            params={
                "period": "7d",
            },
        )

        print_result(
            "14. GRAPH SYSTEM 7d",
            result,
        )

        # ======================================================
        # 15. GRAPH HEAT A 7d
        # ======================================================

        result = await api_get(
            session,
            f"/heatpumps/{WP_ID}/diagrams/graph_heat_a/",
            params={
                "period": "7d",
            },
        )

        print_result(
            "15. GRAPH HEAT A 7d",
            result,
        )

    print()
    print("=" * 100)
    print("DIAGNOSE ABGESCHLOSSEN")
    print("=" * 100)


if __name__ == "__main__":

    asyncio.run(main())