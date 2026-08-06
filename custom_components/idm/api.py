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
        self.session = None


    async def _get_session(self):

        if self.session is None:
            self.session = aiohttp.ClientSession()

        return self.session


    async def login(self):
        """Login using OAuth2."""

        session = await self._get_session()


        url = (
            f"{API_URL}/oauth2/token/"
        )


        payload = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
        }


        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }


        async with session.post(
            url,
            data=payload,
            headers=headers,
            ssl=False,
        ) as response:


            try:
                data = await response.json()

            except Exception:
                data = await response.text()


            _LOGGER.debug(
                "iDM OAuth response %s: %s",
                response.status,
                data,
            )


            if response.status != 200:

                raise Exception(
                    f"OAuth login failed {response.status}: {data}"
                )


            self.token = data.get(
                "access_token"
            )


            if not self.token:

                raise Exception(
                    "No access_token returned"
                )


            _LOGGER.info(
                "iDM OAuth login successful"
            )



    async def _request(
        self,
        endpoint: str,
    ):

        session = await self._get_session()


        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Origin": "https://app.myidm.at",
        }


        async with session.get(
            f"{API_URL}{endpoint}",
            headers=headers,
            ssl=False,
        ) as response:


            response.raise_for_status()

            return await response.json()



    async def get_system_graph(self):

        return await self._request(
            f"/v1/heatpumps/{self.installation}/diagrams/graph_system/?period=24h"
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

        if self.session:

            await self.session.close()

            self.session = None