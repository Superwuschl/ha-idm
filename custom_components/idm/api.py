from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import aiohttp

from homeassistant.core import HomeAssistant


_LOGGER = logging.getLogger(__name__)


class IDMApi:
    """Asynchrone API-Anbindung an myIDM."""

    BASE_URL = "https://a.myidm.at/api/v1"
    WS_URL = "wss://a.myidm.at/ws/navigator-lcd/{wp_id}/"

    # Navigator-Adresse Heizkreis A
    HEAT_A_MODE_ADDRESS = 2002

    # ========================================================
    # SYSTEMMODI
    # ========================================================

    SYSTEM_MODES = {
        0: "Aus",
        1: "Automatik",
        2: "Warmwasser",
        3: "Warmwasser einmal",
    }

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        hass: HomeAssistant,
        access_token: str,
        wp_id: int,
    ) -> None:
        """Initialisiert die API."""

        self.hass = hass
        self.access_token = access_token
        self.wp_id = wp_id

        self._session: aiohttp.ClientSession | None = None

    # ========================================================
    # SESSION
    # ========================================================

    async def _get_session(self) -> aiohttp.ClientSession:
        """Erstellt bzw. liefert die HTTP-Session."""

        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

        return self._session

    # ========================================================
    # HTTP GET
    # ========================================================

    async def _get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> dict:
        """Führt einen authentifizierten GET-Request aus."""

        session = await self._get_session()

        url = f"{self.BASE_URL}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

        _LOGGER.debug(
            "iDM API Request: %s",
            url,
        )

        if params:
            _LOGGER.debug(
                "iDM API Parameter: %s",
                params,
            )

        try:
            async with session.get(
                url,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:

                _LOGGER.debug(
                    "iDM API Antwort HTTP %s",
                    response.status,
                )

                if response.status != 200:
                    text = await response.text()

                    _LOGGER.error(
                        "iDM API Fehler HTTP %s: %s",
                        response.status,
                        text,
                    )

                    raise RuntimeError(
                        f"iDM API HTTP {response.status}"
                    )

                result = await response.json()

                if not isinstance(result, dict):
                    _LOGGER.warning(
                        "iDM API Antwort ist kein Dictionary: %r",
                        result,
                    )
                    return {}

                _LOGGER.debug(
                    "iDM API Antwort Keys: %s",
                    list(result.keys()),
                )

                return result

        except aiohttp.ClientError as err:
            _LOGGER.error(
                "iDM API Verbindungsfehler: %s",
                err,
            )
            raise

        except asyncio.TimeoutError as err:
            _LOGGER.error(
                "iDM API Timeout: %s",
                err,
            )
            raise

    # ========================================================
    # WÄRMEPUMPE
    # ========================================================

    async def heatpump(self) -> dict:
        """Lädt die Stammdaten der Wärmepumpe."""

        endpoint = f"/heatpumps/{self.wp_id}/"

        return await self._get(endpoint)

    # ========================================================
    # DIAGRAMM-DIAGNOSE
    # ========================================================

    @staticmethod
    def _analyze_diagram_data(
        graph_name: str,
        result: dict,
    ) -> None:
        """
        Analysiert die tatsächlich gelieferten Diagrammdaten.

        Die API kann Kanäle in 'channels' deklarieren,
        ohne diese anschließend in den Datenpunkten
        tatsächlich mit einem Wert zu liefern.

        Diese Information wird nur noch zu Debug-Zwecken
        protokolliert. Fehlende deklarierte Kanäle sind kein
        Fehler der API-Verbindung.
        """

        data = result.get("data")

        if not isinstance(data, list) or not data:
            _LOGGER.debug(
                "iDM DIAGNOSE %s: Keine Datenpunkte",
                graph_name,
            )
            return

        # ----------------------------------------------------
        # Zeitinformationen
        # ----------------------------------------------------

        first_point = data[0]
        last_point = data[-1]

        first_datetime = None
        last_datetime = None

        if isinstance(first_point, dict):
            first_datetime = first_point.get("datetime")

        if isinstance(last_point, dict):
            last_datetime = last_point.get("datetime")

        _LOGGER.debug(
            "iDM DIAGNOSE %s: Zeitraum %s -> %s",
            graph_name,
            first_datetime,
            last_datetime,
        )

        # ----------------------------------------------------
        # Alter des letzten Datenpunktes
        # ----------------------------------------------------

        if isinstance(last_point, dict):
            timestamp = last_point.get("timestamp")

            if isinstance(timestamp, (int, float)):
                try:
                    last_timestamp = datetime.fromtimestamp(
                        timestamp,
                        tz=timezone.utc,
                    )

                    now = datetime.now(timezone.utc)

                    age_seconds = (
                        now - last_timestamp
                    ).total_seconds()

                    age_hours = age_seconds / 3600

                    _LOGGER.debug(
                        "iDM DIAGNOSE %s: "
                        "Letzter Datenpunkt ist %.2f Stunden alt",
                        graph_name,
                        age_hours,
                    )

                except (
                    ValueError,
                    OSError,
                    OverflowError,
                ):
                    _LOGGER.debug(
                        "iDM DIAGNOSE %s: "
                        "Timestamp konnte nicht ausgewertet werden: %r",
                        graph_name,
                        timestamp,
                    )

        # ----------------------------------------------------
        # Kanaldefinition der API
        # ----------------------------------------------------

        channels = result.get("channels")

        if not isinstance(channels, list):
            channels = []

        normalized_channels = [
            str(channel)
            for channel in channels
        ]

        _LOGGER.debug(
            "iDM DIAGNOSE %s: "
            "API deklarierte Kanäle=%s",
            graph_name,
            normalized_channels,
        )

        # ----------------------------------------------------
        # Tatsächlich vorhandene Kanäle ermitteln
        # ----------------------------------------------------

        channel_counts: dict[str, int] = {}

        for point in data:
            if not isinstance(point, dict):
                continue

            for key, value in point.items():

                # Metadaten ignorieren
                if key in (
                    "index",
                    "timestamp",
                    "datetime",
                ):
                    continue

                if value is None:
                    continue

                channel_key = str(key)

                channel_counts[channel_key] = (
                    channel_counts.get(channel_key, 0) + 1
                )

        _LOGGER.debug(
            "iDM DIAGNOSE %s: "
            "Tatsächlich gelieferte Kanäle=%s",
            graph_name,
            sorted(channel_counts.keys()),
        )

        _LOGGER.debug(
            "iDM DIAGNOSE %s: "
            "Werteanzahl je Kanal=%s",
            graph_name,
            channel_counts,
        )

        # ----------------------------------------------------
        # Deklarierte aber fehlende Kanäle
        #
        # Wichtig:
        # Nur DEBUG.
        #
        # Die iDM-API liefert beispielsweise Kanal 6 bzw. 16
        # in der Kanaldefinition, aber nicht in den Daten.
        # Das ist für den normalen Betrieb kein Fehler.
        # ----------------------------------------------------

        missing_channels = [
            channel
            for channel in normalized_channels
            if channel not in channel_counts
        ]

        if missing_channels:
            _LOGGER.debug(
                "iDM DIAGNOSE %s: "
                "Deklarierte Kanäle nicht in den Daten vorhanden: %s",
                graph_name,
                missing_channels,
            )

        # ----------------------------------------------------
        # Erster und letzter Datenpunkt
        # ----------------------------------------------------

        _LOGGER.debug(
            "iDM DIAGNOSE %s: "
            "Erster Datenpunkt=%s",
            graph_name,
            first_point,
        )

        _LOGGER.debug(
            "iDM DIAGNOSE %s: "
            "Letzter Datenpunkt=%s",
            graph_name,
            last_point,
        )

    # ========================================================
    # DIAGRAMM
    # ========================================================

    async def _get_diagram(
        self,
        graph_name: str,
        period: str = "24h",
    ) -> dict:
        """Lädt ein iDM Diagramm."""

        endpoint = (
            f"/heatpumps/{self.wp_id}"
            f"/diagrams/{graph_name}/"
        )

        params = {
            "period": period,
        }

        _LOGGER.debug(
            "iDM Diagramm-Anfrage: %s %s",
            graph_name,
            period,
        )

        result = await self._get(
            endpoint,
            params=params,
        )

        data = result.get("data")

        data_count = (
            len(data)
            if isinstance(data, list)
            else 0
        )

        _LOGGER.debug(
            "iDM Diagramm Antwort: "
            "Diagram=%s Angefordert=%s Geliefert=%s Datenpunkte=%s",
            graph_name,
            period,
            result.get("period"),
            data_count,
        )

        channels = result.get("channels")
        channel_labels = result.get("channel_labels")

        _LOGGER.debug(
            "iDM Diagramm Kanaldefinition: "
            "Channels=%s Labels=%s",
            channels,
            channel_labels,
        )

        if data_count:
            _LOGGER.debug(
                "iDM Diagramm erster Datenpunkt: %s",
                data[0],
            )

            _LOGGER.debug(
                "iDM Diagramm letzter Datenpunkt: %s",
                data[-1],
            )

        self._analyze_diagram_data(
            graph_name,
            result,
        )

        return result

    # ========================================================
    # SYSTEM
    # ========================================================

    async def system_graph(
        self,
        period: str = "24h",
    ) -> dict:
        """Lädt das Systemdiagramm."""

        return await self._get_diagram(
            "graph_system",
            period,
        )

    # ========================================================
    # HEIZKREIS A
    # ========================================================

    async def heat_a_graph(
        self,
        period: str = "24h",
    ) -> dict:
        """Lädt das Diagramm von Heizkreis A."""

        return await self._get_diagram(
            "graph_heat_a",
            period,
        )

    # ========================================================
    # HEIZKREIS B
    # ========================================================

    async def heat_b_graph(
        self,
        period: str = "24h",
    ) -> dict:
        """Lädt das Diagramm von Heizkreis B."""

        return await self._get_diagram(
            "graph_heat_b",
            period,
        )

    # ========================================================
    # NAVIGATOR WEBSOCKET
    # ========================================================

    async def _navigator_command(
        self,
        command: dict,
        timeout: float = 10.0,
    ) -> dict:
        """Sendet einen Befehl über den Navigator-WebSocket."""

        session = await self._get_session()

        ws_url = self.WS_URL.format(
            wp_id=self.wp_id
        )

        headers = {
            "Authorization": (
                f"Bearer {self.access_token}"
            ),
            "Origin": "https://a.myidm.at",
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
        }

        _LOGGER.debug(
            "iDM Navigator WebSocket: Verbindung zu %s",
            ws_url,
        )

        _LOGGER.debug(
            "iDM Navigator WebSocket: Befehl=%s",
            command,
        )

        try:
            async with session.ws_connect(
                ws_url,
                headers=headers,
                timeout=timeout,
                heartbeat=30,
            ) as websocket:

                _LOGGER.debug(
                    "iDM Navigator WebSocket Handshake erfolgreich"
                )

                # ------------------------------------------------
                # AUTHENTICATE
                # ------------------------------------------------

                authenticate = {
                    "command": "AUTHENTICATE",
                    "access_token": self.access_token,
                }

                _LOGGER.debug(
                    "iDM Navigator: AUTHENTICATE senden"
                )

                await websocket.send_json(
                    authenticate
                )

                authenticated = False

                async for message in websocket:

                    if message.type == aiohttp.WSMsgType.TEXT:

                        try:
                            response = message.json()

                        except Exception:
                            response = {}

                        _LOGGER.debug(
                            "iDM Navigator Auth Antwort: %s",
                            response,
                        )

                        if (
                            isinstance(response, dict)
                            and (
                                response.get("type") == "image"
                                or response.get("status") == "ok"
                            )
                        ):
                            authenticated = True

                            _LOGGER.debug(
                                "iDM Navigator "
                                "Authentifizierung erfolgreich"
                            )

                            break

                        if (
                            isinstance(response, dict)
                            and response.get("status") == "error"
                        ):
                            raise RuntimeError(
                                "iDM Navigator "
                                f"Authentifizierungsfehler: {response}"
                            )

                    elif message.type == aiohttp.WSMsgType.ERROR:

                        raise RuntimeError(
                            "iDM Navigator WebSocket Fehler"
                        )

                    elif message.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSING,
                    ):

                        raise RuntimeError(
                            "iDM Navigator WebSocket "
                            "wurde während der Authentifizierung "
                            "geschlossen"
                        )

                if not authenticated:
                    raise RuntimeError(
                        "iDM Navigator "
                        "Authentifizierung fehlgeschlagen"
                    )

                # ------------------------------------------------
                # BEFEHL
                # ------------------------------------------------

                _LOGGER.debug(
                    "iDM Navigator Befehl senden: %s",
                    command,
                )

                await websocket.send_json(
                    command
                )

                # ------------------------------------------------
                # ANTWORT
                # ------------------------------------------------

                async for message in websocket:

                    if message.type == aiohttp.WSMsgType.TEXT:

                        try:
                            response = message.json()

                        except Exception:
                            response = {
                                "raw": message.data
                            }

                        _LOGGER.debug(
                            "iDM Navigator Antwort: %s",
                            response,
                        )

                        if isinstance(response, dict):

                            if response.get("status") == "error":
                                raise RuntimeError(
                                    "iDM Navigator Fehler: "
                                    f"{response}"
                                )

                            if response.get("status") == "ok":
                                return response

                            return response

                    elif message.type == aiohttp.WSMsgType.ERROR:

                        raise RuntimeError(
                            "iDM Navigator WebSocket Fehler"
                        )

                    elif message.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSING,
                    ):

                        raise RuntimeError(
                            "iDM Navigator WebSocket "
                            "wurde geschlossen"
                        )

                raise RuntimeError(
                    "iDM Navigator: "
                    "Keine gültige Antwort erhalten"
                )

        except asyncio.TimeoutError:
            _LOGGER.error(
                "iDM Navigator Timeout"
            )
            raise

        except aiohttp.WSServerHandshakeError as err:
            _LOGGER.error(
                "iDM Navigator WebSocket "
                "Handshake fehlgeschlagen: HTTP %s",
                err.status,
            )
            raise

        except aiohttp.ClientError as err:
            _LOGGER.error(
                "iDM Navigator Verbindungsfehler: %s",
                err,
            )
            raise

    # ========================================================
    # NAVIGATOR DIAGNOSE
    # ========================================================

    async def navigator_diagnostic(
        self,
        command: str,
    ) -> dict:
        """Testet einen Navigator-Befehl."""

        if not command:
            raise ValueError(
                "Navigator command darf nicht leer sein"
            )

        test_command = {
            "command": command,
        }

        _LOGGER.debug(
            "iDM Navigator Diagnose: %s",
            test_command,
        )

        return await self._navigator_command(
            test_command
        )

    # ========================================================
    # HEIZKREIS A MODUS SETZEN
    # ========================================================

    async def set_heat_a_mode(
        self,
        mode: int,
    ) -> dict:
        """
        Setzt den Betriebsmodus von Heizkreis A.

        Navigator-Adresse:
            2002
        """

        valid_modes = {
            0: "Aus",
            1: "Zeitprogramm",
            2: "Normal",
            3: "Eco",
            4: "Manuell Heizen",
            5: "Manuell Kühlen",
        }

        if mode not in valid_modes:
            raise ValueError(
                f"Ungültiger Heizkreis-A-Modus: {mode}. "
                f"Erlaubt: {list(valid_modes)}"
            )

        mode_name = valid_modes[mode]

        _LOGGER.info(
            "iDM: Setze Heizkreis A auf '%s' (%s)",
            mode_name,
            mode,
        )

        command = {
            "command": "NC_SET_PARAM",
            "address": self.HEAT_A_MODE_ADDRESS,
            "value": mode,
        }

        result = await self._navigator_command(
            command
        )

        _LOGGER.info(
            "iDM: Heizkreis A erfolgreich auf '%s' (%s) gesetzt",
            mode_name,
            mode,
        )

        return {
            "status": result.get(
                "status",
                "ok",
            ),
            "address": self.HEAT_A_MODE_ADDRESS,
            "value": mode,
            "mode": mode_name,
        }

    # ========================================================
    # SYSTEMMODUS SETZEN
    # ========================================================

    async def set_system_mode(
        self,
        mode: int,
    ) -> dict:
        """
        Setzt den iDM Systemmodus.

        Modi:

            0 = Aus
            1 = Automatik
            2 = Warmwasser
            3 = Warmwasser einmal
        """

        if mode not in self.SYSTEM_MODES:
            raise ValueError(
                f"Ungültiger iDM Systemmodus: {mode}. "
                f"Erlaubt: {list(self.SYSTEM_MODES)}"
            )

        mode_name = self.SYSTEM_MODES[mode]

        _LOGGER.info(
            "iDM: Setze Systemmodus auf '%s' (%s)",
            mode_name,
            mode,
        )

        command = {
            "command": "system_mode",
            "value": mode,
        }

        result = await self._navigator_command(
            command
        )

        _LOGGER.info(
            "iDM: Systemmodus erfolgreich gesetzt",
        )

        return {
            "status": result.get(
                "status",
                "ok",
            ),
            "value": mode,
            "mode": mode_name,
            "response": result,
        }

    # ========================================================
    # SESSION SCHLIESSEN
    # ========================================================

    async def close(self) -> None:
        """Schließt die HTTP-Session."""

        if self._session is not None:

            if not self._session.closed:
                await self._session.close()

            self._session = None