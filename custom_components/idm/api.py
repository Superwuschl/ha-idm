"""API client for iDM integration."""

from __future__ import annotations

import aiohttp
import logging

from .const import API_URL


_LOGGER = logging.getLogger(__name__)


class IDMApi:
    """Client for iDM myIDM API."""

    def __init__(
        self,
        username: str,
        password: str,
        installation: str,
    ) -> None:
        """Initialize API."""

        self.username = username
        self.password = password
        self.installation = installation

        self.token = None


    async def login(self):
        """Login to iDM cloud."""

        async with aiohttp.ClientSession() as session:

            async with session.post(
                f"{API_URL}/api/user/login",
                json={
                    "username": self.username,
                    "password": self.password,
                },
                ssl=False,
            ) as response:

                response.raise_for_status()

                data = await response.json()

                self.token = data.get(
                    "token"
                )

                if not self.token:
                    raise Exception(
                        "No API token received"
                    )



    async def get_values(self):
        """Get all values from iDM."""

        if not self.token:
            await self.login()


        headers = {
            "Authorization": (
                f"Bearer {self.token}"
            )
        }


        async with aiohttp.ClientSession() as session:

            async with session.get(
                f"{API_URL}/api/installation/{self.installation}",
                headers=headers,
                ssl=False,
            ) as response:

                response.raise_for_status()

                data = await response.json()


                _LOGGER.debug(
                    "iDM API response: %s",
                    data,
                )


                return data