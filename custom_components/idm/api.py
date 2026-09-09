from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

import aiohttp

try:
    from homeassistant.core import HomeAssistant
except ModuleNotFoundError:
    HomeAssistant = object


_LOGGER = logging.getLogger(__name__)


class IDMApi:
    """Asynchrone API-Anbindung an myIDM."""

    BASE_URL = "https://a.myidm.at/api/v1"
    WS_URL = "wss://a.myidm.at/ws/navigator-lcd/{wp_id}/"

    # ========================================================
    # NAVIGATOR-ADRESSEN
    # ========================================================

    SYSTEM_MODE_ADDRESS = 2000
    HEAT_A_MODE_ADDRESS = 2002
    HEAT_A_NORMAL_TEMP_ADDRESS = 2016
    HEAT_A_ECO_TEMP_ADDRESS = 2030

    # Anzahl der PNG-Dateien, die während einer Diagnose
    # gespeichert werden
    MAX_NAVIGATOR_IMAGES = 5

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
    # HEIZKREIS-A-MODI
    # ========================================================

    HEAT_A_MODES = {
        0: "Aus",
        1: "Zeitprogramm",
        2: "Normal",
        3: "Eco",
        4: "Manuell Heizen",
        5: "Manuell Kühlen",
    }

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        hass: HomeAssistant,
        access_token: str,
        wp_id: int,
        refresh_token: str | None = None,
    ) -> None:
        """Initialisiert die API."""

        self.hass = hass

        self.access_token = access_token
        self.refresh_token = refresh_token

        self.wp_id = wp_id

        self._session: aiohttp.ClientSession | None = None

        self.auth_expired = False

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

                if response.status == 401:

                    text = await response.text()

                    self.auth_expired = True

                    _LOGGER.error(
                        "iDM API HTTP 401: %s",
                        text,
                    )

                    _LOGGER.error(
                        "iDM API: Access-Token ist abgelaufen. "
                        "Ein automatischer Refresh ist momentan "
                        "noch nicht implementiert."
                    )

                    raise RuntimeError(
                        "iDM API HTTP 401 - "
                        "Session abgelaufen"
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

                self.auth_expired = False

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
    # NAVIGATOR 1.x DASHBOARD
    # ========================================================

    async def navigator_dashboard(self) -> dict:
        """Lädt den aktuellen Navigator-1.x-Dashboardzustand."""

        endpoint = (
            f"/heatpumps/{self.wp_id}"
            "/nav1-0-dashboard/"
        )

        _LOGGER.debug(
            "iDM Navigator Dashboard: Lade %s",
            endpoint,
        )

        result = await self._get(endpoint)

        if not isinstance(result, dict):
            return {}

        _LOGGER.debug(
            "iDM Navigator Dashboard: "
            "Antwort erhalten, Keys=%s",
            list(result.keys()),
        )

        return result

    # ========================================================
    # DIAGRAMM-DIAGNOSE
    # ========================================================

    @staticmethod
    def _analyze_diagram_data(
        graph_name: str,
        result: dict,
    ) -> None:
        """Analysiert die tatsächlich gelieferten Diagrammdaten."""

        data = result.get("data")

        if not isinstance(data, list) or not data:

            _LOGGER.debug(
                "iDM DIAGNOSE %s: Keine Datenpunkte",
                graph_name,
            )

            return

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
                        "Timestamp konnte nicht ausgewertet "
                        "werden: %r",
                        graph_name,
                        timestamp,
                    )

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

        channel_counts: dict[str, int] = {}

        for point in data:

            if not isinstance(point, dict):
                continue

            for key, value in point.items():

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
            "Diagram=%s Angefordert=%s Geliefert=%s "
            "Datenpunkte=%s",
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
            "iDM Navigator WebSocket: "
            "Verbindung zu %s",
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
                    "iDM Navigator WebSocket "
                    "Handshake erfolgreich"
                )

                authenticate = {
                    "command": "AUTHENTICATE",
                    "access_token": self.access_token,
                }

                _LOGGER.debug(
                    "iDM Navigator: "
                    "AUTHENTICATE senden"
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
                                "Authentifizierungsfehler: "
                                f"{response}"
                            )

                    elif message.type == aiohttp.WSMsgType.ERROR:

                        raise RuntimeError(
                            "iDM Navigator "
                            "WebSocket Fehler"
                        )

                    elif message.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSING,
                    ):

                        raise RuntimeError(
                            "iDM Navigator WebSocket "
                            "wurde während der "
                            "Authentifizierung geschlossen"
                        )

                if not authenticated:

                    raise RuntimeError(
                        "iDM Navigator "
                        "Authentifizierung fehlgeschlagen"
                    )

                _LOGGER.debug(
                    "iDM Navigator Befehl senden: %s",
                    command,
                )

                await websocket.send_json(
                    command
                )

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
                            "iDM Navigator "
                            "WebSocket Fehler"
                        )

                    elif message.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSING,
                    ):

                        raise RuntimeError(
                            "iDM Navigator "
                            "WebSocket wurde geschlossen"
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
    # GENERISCHER NAVIGATOR-PARAMETER
    # ========================================================

    async def set_parameter(
        self,
        address: int,
        value: int | float,
    ) -> dict:
        """Setzt einen Navigator-Parameter über NC_SET_PARAM."""

        if not isinstance(address, int):
            raise ValueError(
                "Navigator-Adresse muss eine Ganzzahl sein"
            )

        if not isinstance(value, (int, float)):
            raise ValueError(
                "Navigator-Wert muss numerisch sein"
            )

        command = {
            "command": "NC_SET_PARAM",
            "address": address,
            "value": value,
        }

        _LOGGER.warning(
            "iDM DIAGNOSE WRITE: "
            "Sende NC_SET_PARAM Adresse=%s Wert=%s",
            address,
            value,
        )

        result = await self._navigator_command(
            command
        )

        _LOGGER.warning(
            "iDM DIAGNOSE WRITE: Antwort=%s",
            result,
        )

        return {
            "status": result.get(
                "status",
                "ok",
            ),
            "address": address,
            "value": value,
            "response": result,
        }

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
    # PNG-SPEICHERUNG
    # ========================================================

    def _get_navigator_image_directory(self) -> Path:
        """
        Liefert das Verzeichnis für die Navigator-PNG-Dateien.

        Unter Home Assistant wird /config verwendet.
        Außerhalb von Home Assistant wird das aktuelle
        Arbeitsverzeichnis verwendet.
        """

        try:
            config_path = self.hass.config.path(
                "navigator_images"
            )

        except Exception:

            config_path = str(
                Path.cwd() / "navigator_images"
            )

        directory = Path(config_path)

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    @staticmethod
    def _is_png(data: bytes) -> bool:
        """Prüft anhand der PNG-Signatur, ob die Daten PNG sind."""

        png_signature = b"\x89PNG\r\n\x1a\n"

        return data.startswith(png_signature)

    def _save_navigator_png(
        self,
        data: bytes,
        image_number: int,
    ) -> str | None:
        """Speichert ein empfangenes PNG."""

        if not data:

            _LOGGER.warning(
                "iDM Navigator PNG: "
                "Leere Binärnachricht erhalten"
            )

            return None

        if not self._is_png(data):

            _LOGGER.warning(
                "iDM Navigator PNG: "
                "Binärnachricht ist kein PNG "
                "(Größe=%d Bytes, Signatur=%r)",
                len(data),
                data[:16],
            )

            return None

        directory = self._get_navigator_image_directory()

        filename = (
            f"navigator_{image_number:02d}.png"
        )

        filepath = directory / filename

        try:

            filepath.write_bytes(data)

        except OSError as err:

            _LOGGER.error(
                "iDM Navigator PNG: "
                "Datei konnte nicht gespeichert werden: "
                "%s",
                err,
            )

            return None

        _LOGGER.warning(
            "iDM Navigator PNG gespeichert: "
            "%s (%d Bytes)",
            filepath,
            len(data),
        )

        return str(filepath)

    # ========================================================
    # NAVIGATOR LISTENER
    # ========================================================

    async def navigator_listen(
        self,
        duration: float = 5.0,
    ) -> dict:
        """
        Öffnet eine Navigator-WebSocket-Verbindung und
        protokolliert alle eingehenden Nachrichten.

        Zusätzlich werden bis zu fünf empfangene PNG-Dateien
        unter /config/navigator_images gespeichert.

        Diese Funktion verändert keinen Parameter.
        """

        if duration <= 0:

            raise ValueError(
                "Die Diagnose-Dauer muss größer als 0 sein"
            )

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

        messages = []
        saved_images = []

        _LOGGER.warning(
            "iDM DIAGNOSE LISTENER: "
            "Starte Navigator-Listener für %.1f Sekunden",
            duration,
        )

        _LOGGER.warning(
            "iDM DIAGNOSE LISTENER: "
            "Bis zu %d PNG-Dateien werden gespeichert.",
            self.MAX_NAVIGATOR_IMAGES,
        )

        try:

            async with session.ws_connect(
                ws_url,
                headers=headers,
                timeout=10,
                heartbeat=30,
            ) as websocket:

                authenticate = {
                    "command": "AUTHENTICATE",
                    "access_token": self.access_token,
                }

                _LOGGER.warning(
                    "iDM DIAGNOSE LISTENER: "
                    "Sende AUTHENTICATE"
                )

                await websocket.send_json(
                    authenticate
                )

                authenticated = False

                try:

                    message = await asyncio.wait_for(
                        websocket.receive(),
                        timeout=10,
                    )

                except asyncio.TimeoutError:

                    raise RuntimeError(
                        "Timeout während "
                        "Navigator-Authentifizierung"
                    )

                if message.type == aiohttp.WSMsgType.TEXT:

                    try:
                        response = message.json()

                    except Exception:
                        response = {
                            "raw": message.data
                        }

                    _LOGGER.warning(
                        "iDM DIAGNOSE LISTENER: "
                        "AUTH Antwort=%s",
                        response,
                    )

                    messages.append(response)

                    if (
                        isinstance(response, dict)
                        and (
                            response.get("type") == "image"
                            or response.get("status") == "ok"
                        )
                    ):

                        authenticated = True

                elif message.type == aiohttp.WSMsgType.BINARY:

                    _LOGGER.warning(
                        "iDM DIAGNOSE LISTENER: "
                        "AUTH Antwort ist BINÄR, Länge=%d",
                        len(message.data),
                    )

                    image_path = None

                    if (
                        len(saved_images)
                        < self.MAX_NAVIGATOR_IMAGES
                    ):

                        image_path = self._save_navigator_png(
                            message.data,
                            len(saved_images) + 1,
                        )

                        if image_path:
                            saved_images.append(
                                image_path
                            )

                    messages.append(
                        {
                            "type": "binary",
                            "length": len(message.data),
                            "png": image_path is not None,
                            "file": image_path,
                        }
                    )

                    authenticated = True

                if not authenticated:

                    raise RuntimeError(
                        "Navigator-Authentifizierung "
                        "für Listener fehlgeschlagen"
                    )

                _LOGGER.warning(
                    "iDM DIAGNOSE LISTENER: "
                    "Authentifizierung erfolgreich. "
                    "Warte auf weitere Nachrichten."
                )

                end_time = (
                    asyncio.get_running_loop().time()
                    + duration
                )

                while True:

                    remaining = (
                        end_time
                        - asyncio.get_running_loop().time()
                    )

                    if remaining <= 0:
                        break

                    try:

                        message = await asyncio.wait_for(
                            websocket.receive(),
                            timeout=remaining,
                        )

                    except asyncio.TimeoutError:

                        break

                    if message.type == aiohttp.WSMsgType.TEXT:

                        try:
                            response = message.json()

                        except Exception:
                            response = {
                                "raw": message.data
                            }

                        _LOGGER.warning(
                            "iDM DIAGNOSE LISTENER: "
                            "Eingehende Nachricht=%s",
                            response,
                        )

                        messages.append(response)

                    elif message.type == aiohttp.WSMsgType.BINARY:

                        data = message.data

                        _LOGGER.warning(
                            "iDM DIAGNOSE LISTENER: "
                            "BINÄR-Nachricht Länge=%d",
                            len(data),
                        )

                        image_path = None

                        if (
                            len(saved_images)
                            < self.MAX_NAVIGATOR_IMAGES
                        ):

                            image_path = self._save_navigator_png(
                                data,
                                len(saved_images) + 1,
                            )

                            if image_path:

                                saved_images.append(
                                    image_path
                                )

                        else:

                            _LOGGER.warning(
                                "iDM Navigator PNG: "
                                "Maximale Anzahl von %d Dateien "
                                "bereits gespeichert.",
                                self.MAX_NAVIGATOR_IMAGES,
                            )

                        messages.append(
                            {
                                "type": "binary",
                                "length": len(data),
                                "png": self._is_png(data),
                                "file": image_path,
                            }
                        )

                    elif message.type == aiohttp.WSMsgType.ERROR:

                        _LOGGER.warning(
                            "iDM DIAGNOSE LISTENER: "
                            "WebSocket Fehler=%s",
                            websocket.exception(),
                        )

                        break

                    elif message.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSING,
                    ):

                        _LOGGER.warning(
                            "iDM DIAGNOSE LISTENER: "
                            "WebSocket geschlossen"
                        )

                        break

        except asyncio.TimeoutError:

            _LOGGER.error(
                "iDM DIAGNOSE LISTENER: Timeout"
            )

            raise

        except aiohttp.WSServerHandshakeError as err:

            _LOGGER.error(
                "iDM DIAGNOSE LISTENER: "
                "Handshake fehlgeschlagen HTTP %s",
                err.status,
            )

            raise

        except aiohttp.ClientError as err:

            _LOGGER.error(
                "iDM DIAGNOSE LISTENER: "
                "Verbindungsfehler: %s",
                err,
            )

            raise

        _LOGGER.warning(
            "iDM DIAGNOSE LISTENER: "
            "Beendet. %d Nachrichten empfangen. "
            "%d PNG-Dateien gespeichert.",
            len(messages),
            len(saved_images),
        )

        if saved_images:

            _LOGGER.warning(
                "iDM DIAGNOSE LISTENER: "
                "Gespeicherte PNG-Dateien=%s",
                saved_images,
            )

        return {
            "status": "ok",
            "messages": messages,
            "images": saved_images,
            "image_count": len(saved_images),
        }

    # ========================================================
    # PARAMETER LESEN
    # ========================================================

    async def navigator_read_param(
        self,
        address: int,
    ) -> dict:
        """
        DEAKTIVIERT.

        NC_GET_PARAM wird momentan nicht verwendet,
        da der Navigator diesen Befehl mit
        'unknown command' zurückgewiesen hat.
        """

        if not isinstance(address, int):

            raise ValueError(
                "Navigator-Adresse muss eine Ganzzahl sein"
            )

        _LOGGER.warning(
            "iDM DIAGNOSE READ: "
            "Direktes Lesen von Adresse %s ist momentan "
            "nicht implementiert.",
            address,
        )

        return {
            "status": "not_supported",
            "address": address,
            "reason": (
                "NC_GET_PARAM wurde vom Navigator "
                "mit 'unknown command' abgelehnt."
            ),
        }

    # ========================================================
    # HEIZKREIS A MODUS SETZEN
    # ========================================================

    async def set_heat_a_mode(
        self,
        mode: int,
    ) -> dict:
        """Setzt den Betriebsmodus von Heizkreis A."""

        if mode not in self.HEAT_A_MODES:

            raise ValueError(
                f"Ungültiger Heizkreis-A-Modus: {mode}. "
                f"Erlaubt: {list(self.HEAT_A_MODES)}"
            )

        mode_name = self.HEAT_A_MODES[mode]

        _LOGGER.warning(
            "iDM: Setze Heizkreis A auf '%s' (%s)",
            mode_name,
            mode,
        )

        result = await self.set_parameter(
            self.HEAT_A_MODE_ADDRESS,
            mode,
        )

        _LOGGER.warning(
            "iDM DIAGNOSE: "
            "Heizkreis A Schreiben abgeschlossen. "
            "Soll=%s (%s)",
            mode,
            mode_name,
        )

        return {
            "status": result.get(
                "status",
                "ok",
            ),
            "address": self.HEAT_A_MODE_ADDRESS,
            "value": mode,
            "mode": mode_name,
            "readback": {
                "status": "not_available",
                "reason": (
                    "NC_GET_PARAM wird vom Navigator "
                    "nicht unterstützt."
                ),
            },
            "response": result.get(
                "response",
                result,
            ),
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

        Navigator-Adresse:
            2000
        """

        if mode not in self.SYSTEM_MODES:

            raise ValueError(
                f"Ungültiger iDM Systemmodus: {mode}. "
                f"Erlaubt: {list(self.SYSTEM_MODES)}"
            )

        mode_name = self.SYSTEM_MODES[mode]

        _LOGGER.warning(
            "iDM: Setze Systemmodus auf '%s' (%s)",
            mode_name,
            mode,
        )

        result = await self.set_parameter(
            self.SYSTEM_MODE_ADDRESS,
            mode,
        )

        _LOGGER.warning(
            "iDM: Systemmodus erfolgreich gesetzt"
        )

        return {
            "status": result.get(
                "status",
                "ok",
            ),
            "address": self.SYSTEM_MODE_ADDRESS,
            "value": mode,
            "mode": mode_name,
            "response": result.get(
                "response",
                result,
            ),
        }

    # ========================================================
    # HEIZKREIS A NORMALTEMPERATUR
    # ========================================================

    async def set_heat_a_normal_temperature(
        self,
        value: float,
    ) -> dict:
        """Setzt die normale Raum-Solltemperatur von Heizkreis A."""

        value = float(value)

        if value < 15.0 or value > 30.0:
            raise ValueError(
                "Heizkreis-A-Normaltemperatur muss "
                "zwischen 15.0 und 30.0 °C liegen."
            )

        rounded = round(value * 2) / 2

        if abs(value - rounded) > 0.001:
            raise ValueError(
                "Heizkreis-A-Normaltemperatur muss "
                "in 0.5-°C-Schritten angegeben werden."
            )

        return await self.set_parameter(
            self.HEAT_A_NORMAL_TEMP_ADDRESS,
            value,
        )

    # ========================================================
    # HEIZKREIS A ECO-TEMPERATUR
    # ========================================================

    async def set_heat_a_eco_temperature(
        self,
        value: float,
    ) -> dict:
        """Setzt die Eco-Raum-Solltemperatur von Heizkreis A."""

        value = float(value)

        if value < 10.0 or value > 25.0:
            raise ValueError(
                "Heizkreis-A-Eco-Temperatur muss "
                "zwischen 10.0 und 25.0 °C liegen."
            )

        rounded = round(value * 2) / 2

        if abs(value - rounded) > 0.001:
            raise ValueError(
                "Heizkreis-A-Eco-Temperatur muss "
                "in 0.5-°C-Schritten angegeben werden."
            )

        return await self.set_parameter(
            self.HEAT_A_ECO_TEMP_ADDRESS,
            value,
        )

    # ========================================================
    # DIREKTE ALIASE
    # ========================================================

    async def get_system_graph_data(
        self,
        period: str = "24h",
    ) -> dict:
        """Alias für system_graph()."""

        return await self.system_graph(
            period
        )

    async def get_heat_a_graph_data(
        self,
        period: str = "24h",
    ) -> dict:
        """Alias für heat_a_graph()."""

        return await self.heat_a_graph(
            period
        )

    async def get_heat_b_graph_data(
        self,
        period: str = "24h",
    ) -> dict:
        """Alias für heat_b_graph()."""

        return await self.heat_b_graph(
            period
        )

    # ========================================================
    # AUTH STATUS
    # ========================================================

    def is_authenticated(self) -> bool:
        """Gibt zurück, ob die letzte HTTP-Anfrage authentifiziert war."""

        return not self.auth_expired

    # ========================================================
    # SESSION SCHLIESSEN
    # ========================================================

    async def close(self) -> None:
        """Schließt die HTTP-Session."""

        if self._session is not None:

            if not self._session.closed:

                _LOGGER.debug(
                    "iDM API: Schließe aiohttp ClientSession"
                )

                await self._session.close()

            self._session = None

        _LOGGER.debug(
            "iDM API: Session geschlossen"
        )