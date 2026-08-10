import asyncio
import importlib.util
import sys

import aiohttp


# ============================================================
# KONFIGURATION
# ============================================================

ACCESS_TOKEN = "OmuGrETkbh9TANzpvY1POv2vDt9kr6"

REFRESH_TOKEN = "Xbd6NT7QUvkOoY8bqHfLzitWM7s15r"

WP_ID = 3419


# ============================================================
# API.PY DIREKT LADEN
#
# Dadurch benötigen wir kein installiertes Home Assistant.
# ============================================================

API_FILE = (
    r"C:\Users\Bernd\Documents\ha-idm"
    r"\custom_components\idm\api.py"
)


spec = importlib.util.spec_from_file_location(
    "idm_api",
    API_FILE,
)


if spec is None or spec.loader is None:
    raise RuntimeError(
        f"api.py konnte nicht geladen werden:\n"
        f"{API_FILE}"
    )


module = importlib.util.module_from_spec(spec)

sys.modules["idm_api"] = module

spec.loader.exec_module(module)

IDMApi = module.IDMApi


# ============================================================
# TEST
# ============================================================

async def main():

    print()
    print("=" * 60)
    print("iDM HEIZKREIS A SCHREIBTEST")
    print("=" * 60)

    print()
    print(f"Wärmepumpe: {WP_ID}")
    print(
        f"Access-Token Länge: "
        f"{len(ACCESS_TOKEN)}"
    )

    # ========================================================
    # HTTP / WEBSOCKET SESSION
    # ========================================================

    async with aiohttp.ClientSession() as session:

        api = IDMApi(
            session=session,
            access_token=ACCESS_TOKEN,
            refresh_token=REFRESH_TOKEN,
            wp_id=WP_ID,
        )

        # ====================================================
        # 1. AKTUELLEN MODUS LESEN
        # ====================================================

        print()
        print("-" * 60)
        print("1. AKTUELLEN MODUS LESEN")
        print("-" * 60)

        try:

            current_mode = (
                await api.get_heat_a_mode()
            )

            print()
            print(
                f"Aktueller Heizkreis-A-Modus: "
                f"{current_mode}"
            )

        except Exception as err:

            print()
            print(
                "FEHLER BEIM LESEN DES AKTUELLEN MODUS:"
            )

            print(
                f"{type(err).__name__}: {err}"
            )

            return

        # ====================================================
        # 2. SICHERHEITSPRÜFUNG
        #
        # Wir schreiben nur dann 2 = ECO, wenn der aktuelle
        # Modus ebenfalls 2 ist.
        #
        # Dadurch vermeiden wir, dass dieser Test versehentlich
        # einen anderen Betriebsmodus verändert.
        # ====================================================

        print()
        print("-" * 60)
        print("2. SICHERHEITSPRÜFUNG")
        print("-" * 60)

        if current_mode != 2:

            print()
            print(
                "SCHREIBTEST ABGEBROCHEN!"
            )

            print(
                "Der aktuelle Heizkreis-A-Modus "
                f"ist {current_mode}."
            )

            print(
                "Erwartet wurde 2 = ECO."
            )

            print()
            print(
                "Es wurde KEIN Schreibbefehl "
                "an die Wärmepumpe gesendet."
            )

            return

        print()
        print(
            "Aktueller Modus = 2"
        )

        print(
            "2 entspricht ECO."
        )

        print(
            "Sicherheitsprüfung erfolgreich."
        )

        # ====================================================
        # 3. SCHREIBTEST
        #
        # Wir schreiben bewusst denselben Wert:
        #
        # address = 2002
        # value   = 2
        #
        # Damit wird ECO -> ECO geschrieben.
        # ====================================================

        print()
        print("-" * 60)
        print("3. SCHREIBTEST: ECO -> ECO")
        print("-" * 60)

        print()
        print(
            "Adresse: 2002"
        )

        print(
            "Wert: 2"
        )

        print(
            "Bedeutung: ECO"
        )

        print()
        print(
            "Sende NC_SET_PARAM..."
        )

        try:

            result = await api.set_heat_a_mode(
                2
            )

            print()
            print(
                "SCHREIBERGEBNIS:"
            )

            print(
                result
            )

        except Exception as err:

            print()
            print(
                "SCHREIBEN FEHLGESCHLAGEN:"
            )

            print(
                f"Fehlertyp: "
                f"{type(err).__name__}"
            )

            print(
                f"Fehler: {err}"
            )

            return

        # ====================================================
        # 4. MODUS NACH DEM SCHREIBEN ERNEUT LESEN
        # ====================================================

        print()
        print("-" * 60)
        print("4. MODUS NACH DEM SCHREIBEN LESEN")
        print("-" * 60)

        try:

            new_mode = (
                await api.get_heat_a_mode()
            )

            print()
            print(
                "Heizkreis-A-Modus nach Schreiben:"
            )

            print(
                new_mode
            )

        except Exception as err:

            print()
            print(
                "LESEN NACH SCHREIBEN FEHLGESCHLAGEN:"
            )

            print(
                f"Fehlertyp: "
                f"{type(err).__name__}"
            )

            print(
                f"Fehler: {err}"
            )

            return

        # ====================================================
        # 5. ERGEBNIS BEWERTEN
        # ====================================================

        print()
        print("-" * 60)
        print("5. ERGEBNIS")
        print("-" * 60)

        if new_mode == 2:

            print()
            print(
                "SCHREIBTEST ERFOLGREICH."
            )

            print()
            print(
                "Der Heizkreis-A-Modus ist weiterhin:"
            )

            print(
                "2 = ECO"
            )

            print()
            print(
                "Damit sind bestätigt:"
            )

            print(
                "  [OK] WebSocket-Verbindung"
            )

            print(
                "  [OK] WebSocket-Authentifizierung"
            )

            print(
                "  [OK] NC_SET_PARAM"
            )

            print(
                "  [OK] Adresse 2002"
            )

            print(
                "  [OK] Wert 2"
            )

            print(
                "  [OK] Rücklesen über API"
            )

        else:

            print()
            print(
                "WARNUNG:"
            )

            print(
                "Der zurückgelesene Modus entspricht "
                "nicht dem geschriebenen Wert."
            )

            print(
                f"Geschrieben: 2"
            )

            print(
                f"Gelesen:     {new_mode}"
            )


# ============================================================
# PROGRAMMSTART
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print()
        print(
            "Test durch Benutzer abgebrochen."
        )