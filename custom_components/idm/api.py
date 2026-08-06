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
        access_token: str,
    ) -> None:
        """Initialize API client."""

        self.username = username
        self.password = password
        self.installation = installation
        self.heatpump = installation
        self.token = access_token

        self.base_url = API_URL
        self.session = None


    async def login(self):
        """Validate access token."""

        if not self.token:
            raise Exception(
                "No iDM Access-Token available"
            )

        self.session = aiohttp.ClientSession()

        try:
            await self._request(
                "/users/current"
            )

            _LOGGER.debug(
                "iDM API authentication successful"
            )

        except Exception:
            await self.close()
            raise


    async def close(self):
        """Close API session."""

        if self.session:

            await self.session.close()

            self.session = None


    async def _request(
        self,
        endpoint: str,
    ):
        """Send API request."""

        if self.session is None:

            self.session = aiohttp.ClientSession()


        headers = {
            "Authorization": f"Access-Token {self.token}",
            "Content-Type": "application/json",
            "Origin": "https://app.myidm.at",
        }


        url = (
            f"{self.base_url}{endpoint}"
        )


        async with self.session.get(
            url,
            headers=headers,
            ssl=False,
        ) as response:

            response.raise_for_status()

            return await response.json()


    async def get_system_graph(self):
        """Get system diagram data."""

        return await self._request(
            f"/heatpumps/{self.heatpump}/diagrams/graph_system/?period=24h"
        )


    async def get_values(self):
        """Return latest heatpump values."""

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