from __future__ import annotations

import logging

from aiohttp import ClientSession


BASE_URL = "https://a.myidm.at"

_LOGGER = logging.getLogger(__name__)


class IDMApi:

    def __init__(
        self,
        session: ClientSession,
        access_token: str,
        refresh_token: str | None,
        wp_id: int,
    ):

        self.session = session
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.wp_id = wp_id


    def _headers(self):

        return {
            "Authorization": f"Access-Token {self.access_token}",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://app.myidm.at",
            "Referer": "https://app.myidm.at/",
            "User-Agent": "Mozilla/5.0",
        }


    async def refresh(self):

        url = BASE_URL + "/api/v1/oauth2/token/"

        data = {
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }

        _LOGGER.warning(
            "iDM Refresh Token wird verwendet"
        )

        async with self.session.post(
            url,
            data=data,
            timeout=20,
        ) as response:

            _LOGGER.warning(
                "iDM Refresh Antwort HTTP %s",
                response.status,
            )

            response.raise_for_status()

            token = await response.json()

        self.access_token = token["access_token"]

        if "refresh_token" in token:
            self.refresh_token = token["refresh_token"]

        _LOGGER.warning(
            "iDM Access Token erfolgreich erneuert"
        )

        return token


    async def get(self, endpoint):

        url = BASE_URL + endpoint

        _LOGGER.warning(
            "iDM API Request: %s | Token Länge: %s",
            url,
            len(self.access_token),
        )

        async with self.session.get(
            url,
            headers=self._headers(),
            timeout=20,
        ) as response:

            _LOGGER.warning(
                "iDM API Antwort HTTP %s",
                response.status,
            )

            if response.status == 401:

                _LOGGER.warning(
                    "iDM HTTP 401 - starte Token Refresh"
                )

                await self.refresh()

                async with self.session.get(
                    url,
                    headers=self._headers(),
                    timeout=20,
                ) as retry_response:

                    _LOGGER.warning(
                        "iDM Wiederholungsversuch HTTP %s",
                        retry_response.status,
                    )

                    retry_response.raise_for_status()

                    return await retry_response.json()

            response.raise_for_status()

            return await response.json()


    async def heatpump(self):

        return await self.get(
            f"/api/v1/heatpumps/{self.wp_id}/"
        )


    async def diagrams(self):

        return await self.get(
            f"/api/v1/heatpumps/{self.wp_id}/diagrams/"
        )


    async def system_graph(self):

        return await self.get(
            f"/api/v1/heatpumps/{self.wp_id}/diagrams/graph_system/?period=24h"
        )


    async def heat_a_graph(self):

        return await self.get(
            f"/api/v1/heatpumps/{self.wp_id}/diagrams/graph_heat_a/?period=24h"
        )


    async def heat_b_graph(self):

        return await self.get(
            f"/api/v1/heatpumps/{self.wp_id}/diagrams/graph_heat_b/?period=24h"
        )