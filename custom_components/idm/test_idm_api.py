import json
import time
import websocket


# ============================================================
# iDM Einstellungen
# ============================================================

ACCESS_TOKEN = "5Sduw4nSKLIzK1ffMf3FDcKQ3DzHfo"
WP_ID = 3419

WS_URL = f"wss://a.myidm.at/ws/navigator-lcd/{WP_ID}/"


# ============================================================
# Heizkreis-Modi
# ============================================================

MODES = {
    0: "Aus",
    1: "Zeitprogramm",
    2: "Normal",
    3: "Eco",
    4: "Manuell Heizen",
    5: "Manuell Kühlen",
}


# ============================================================
# TESTWERT
#
# 0 = Aus
# 1 = Zeitprogramm
# 2 = Normal
# 3 = Eco
# 4 = Manuell Heizen
# 5 = Manuell Kühlen
# ============================================================

TEST_VALUE = 2


# ============================================================
# WebSocket Test
# ============================================================

def test_heating_circuit_mode(value):
    mode_name = MODES.get(value, "UNBEKANNT")

    print()
    print("=" * 60)
    print(" iDM Heizkreis A - Schreibtest")
    print("=" * 60)

    print()
    print("Modi:")
    print()
    for number, name in MODES.items():
        print(f"{number} = {name}")

    print()
    print("Wir testen jetzt:")
    print(f"{value} = {mode_name}")

    print()
    print("=" * 60)
    print(f"Setze Heizkreis A auf: {mode_name}")
    print(f"Wert: {value}")
    print("=" * 60)

    print()
    print("Verbinde mit:")
    print(WS_URL)

    try:

        # ----------------------------------------------------
        # WebSocket Verbindung
        # ----------------------------------------------------

        ws = websocket.create_connection(
            WS_URL,
            timeout=10,
        )

        print("WebSocket verbunden.")

        # ----------------------------------------------------
        # Authentifizierung
        # ----------------------------------------------------

        print()
        print("Authentifiziere WebSocket...")

        auth_message = {
            "command": "AUTHENTICATE",
            "access_token": ACCESS_TOKEN,
        }

        ws.send(json.dumps(auth_message))

        print()
        print("Warte auf Authentifizierungs-Antwort...")

        authenticated = False

        # Wir können mehrere Nachrichten bekommen.
        # Die erste relevante Antwort ist häufig das LCD-Bild.
        auth_deadline = time.time() + 10

        while time.time() < auth_deadline:

            try:
                raw_response = ws.recv()

            except websocket.WebSocketTimeoutException:
                continue

            if not raw_response:
                continue

            print()
            print("WebSocket Antwort:")
            print(raw_response[:500])

            try:
                response = json.loads(raw_response)

            except json.JSONDecodeError:
                print("Antwort ist kein JSON.")
                continue

            # ------------------------------------------------
            # AUTHENTIFIZIERUNG ERFOLGREICH
            #
            # Der iDM WebSocket liefert nach erfolgreicher
            # Authentifizierung offenbar ein LCD-Bild:
            #
            # {
            #   "type": "image",
            #   "data": "data:image/png;base64,..."
            # }
            # ------------------------------------------------

            if response.get("type") == "image":

                print()
                print("==================================================")
                print("AUTHENTIFIZIERUNG ERFOLGREICH")
                print("==================================================")

                print("iDM hat ein LCD-Bild geliefert.")
                print("WebSocket ist authentifiziert.")

                authenticated = True
                break

            # ------------------------------------------------
            # Mögliche explizite Auth-Antwort
            # ------------------------------------------------

            if response.get("status") == "ok":

                print()
                print("==================================================")
                print("AUTHENTIFIZIERUNG ERFOLGREICH")
                print("==================================================")

                authenticated = True
                break

            # ------------------------------------------------
            # Authentifizierungsfehler
            # ------------------------------------------------

            if response.get("status") == "error":

                message = response.get("message", "")

                print()
                print("==================================================")
                print("WEBSOCKET FEHLER")
                print("==================================================")

                print(f"Nachricht: {message}")

                if "authentication" in message.lower():
                    print()
                    print("Authentifizierung wurde vom Server abgelehnt.")

                ws.close()
                return False

        # ----------------------------------------------------
        # Keine Authentifizierung erkannt
        # ----------------------------------------------------

        if not authenticated:

            print()
            print("==================================================")
            print("AUTHENTIFIZIERUNG NICHT BESTÄTIGT")
            print("==================================================")

            print("Innerhalb des Zeitlimits wurde keine")
            print("gültige Authentifizierungsantwort erkannt.")

            ws.close()
            return False

        # ----------------------------------------------------
        # NC_SET_PARAM
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("Sende NC_SET_PARAM")
        print("=" * 60)

        command = {
            "command": "NC_SET_PARAM",
            "address": 2002,
            "value": value,
        }

        print()
        print("Befehl:")
        print(json.dumps(command, indent=2))

        ws.send(json.dumps(command))

        print()
        print("Befehl gesendet.")
        print("Warte auf Antwort...")

        # ----------------------------------------------------
        # Antwort auf Schreibbefehl
        # ----------------------------------------------------

        write_deadline = time.time() + 10

        while time.time() < write_deadline:

            try:
                raw_response = ws.recv()

            except websocket.WebSocketTimeoutException:
                print("Noch keine Antwort...")
                continue

            if not raw_response:
                continue

            print()
            print("Antwort vom iDM WebSocket:")
            print(raw_response[:1000])

            try:
                response = json.loads(raw_response)

            except json.JSONDecodeError:
                print("Antwort ist kein JSON.")
                continue

            # ------------------------------------------------
            # OK
            # ------------------------------------------------

            if response.get("status") == "ok":

                print()
                print("=" * 60)
                print("SCHREIBBEFEHL ERFOLGREICH")
                print("=" * 60)

                print()
                print(f"Heizkreis A wurde auf '{mode_name}' gesetzt.")
                print(f"Adresse: 2002")
                print(f"Wert:    {value}")

                ws.close()

                print()
                print("WebSocket geschlossen.")

                return True

            # ------------------------------------------------
            # Fehler
            # ------------------------------------------------

            if response.get("status") == "error":

                print()
                print("=" * 60)
                print("SCHREIBBEFEHL FEHLGESCHLAGEN")
                print("=" * 60)

                print()
                print(f"Fehlermeldung: {response.get('message')}")

                ws.close()

                return False

        # ----------------------------------------------------
        # Timeout
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("KEINE ANTWORT AUF NC_SET_PARAM")
        print("=" * 60)

        ws.close()

        return False

    except Exception as e:

        print()
        print("=" * 60)
        print("FEHLER")
        print("=" * 60)

        print(type(e).__name__)
        print(str(e))

        return False


# ============================================================
# Hauptprogramm
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print(" iDM Heizkreis A - WebSocket Test")
    print("=" * 60)

    print()
    print(f"WP-ID:       {WP_ID}")
    print(f"WebSocket:   {WS_URL}")
    print(f"Testwert:    {TEST_VALUE}")
    print(f"Testmodus:   {MODES.get(TEST_VALUE, 'UNBEKANNT')}")

    print()

    if ACCESS_TOKEN == "DEIN_ACCESS_TOKEN":

        print("=" * 60)
        print("FEHLER: ACCESS_TOKEN NICHT EINGETRAGEN")
        print("=" * 60)

        print()
        print("Bitte oben im Skript deinen Token eintragen:")
        print()
        print('ACCESS_TOKEN = "DEIN_TOKEN"')
        print()

    else:

        success = test_heating_circuit_mode(TEST_VALUE)

        print()

        if success:

            print("=" * 60)
            print("TEST ERFOLGREICH")
            print("=" * 60)

        else:

            print("=" * 60)
            print("TEST NICHT ERFOLGREICH")
            print("=" * 60)

        print()
