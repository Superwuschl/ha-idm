"""API client for iDM integration."""

from __future__ import annotations

import logging

import aiohttp

from .const import API_URL


_LOGGER = logging.getLogger(__name__)


class IDMApi:
    """Client for iDM API."""

    def __init__(
        self,
        username: str,
        password: str,
        installation: str,
    ) -> None:
        """Initialize."""

        self.username = username
        self.password = password
        self.installation = installation

        self.token = None
        self.session = aiohttp.ClientSession()


    async def login(self):
        """Get OAuth2 access token."""

        url = (
            f"{API_URL}/oauth2/token/"
        )


        payload = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
        }


        headers = {
            "Content-Type": "application/json",
        }


        async with self.session.post(
            url,
            json=payload,
            headers=headers,
            ssl=False,
        ) as response:

            data = await response.json()


            if response.status != 200:

                raise Exception(
                    f"iDM OAuth login failed: {response.status} {data}"
                )


            self.token = data.get(
                "access_token"
            )


            if not self.token:

                raise Exception(
                    "No access_token returned"
                )


            _LOGGER.debug(
                "iDM OAuth login successful"
            )


    async def _request(
        self,
        endpoint: str,
    ):

        headers = {
            "Authorization": f"Access-Token {self.token}",
            "Content-Type": "application/json",
        }


        async with self.session.get(
            f"{API_URL}{endpoint}",
            headers=headers,
            ssl=False,
        ) as response:

            response.raise_for_status()

            return await response.json()


    async def get_system_graph(self):

        return await self._request(
            f"/heatpumps/{self.installation}/diagrams/graph_system/?period=24h"
        )


    async def get_values(self):

        data = await self.get_system_graph()

        result = {}


        labels = data.get(
            "channel_labels",
            {},
        )

        points = data.get(
            "data",
            [],
        )


        if not points:
            return result


        latest = points[-1]


        for channel, name in labels.items():

            value = latest.get(
                str(channel)
            )

            if value is not None:

                result[name] = value


        return result


    async def close(self):

        await self.session.close()