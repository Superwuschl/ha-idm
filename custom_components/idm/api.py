"""API client for iDM integration."""

from __future__ import annotations

import logging

import aiohttp

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
        """Login to iDM."""

        urls = [
            "/api/user/login",
            "/api/auth/login",
            "/api/login",
            "/api/v1/login",
        ]

        async with aiohttp.ClientSession() as session:

            for path in urls:

                url = f"{API_URL}{path}"

                try:

                    async with session.post(
                        url,
                        json={
                            "username": self.username,
                            "password": self.password,
                        },
                        ssl=False,
                    ) as response:

                        text = await response.text()

                        _LOGGER.warning(
                            "iDM login test %s -> %s: %s",
                            path,
                            response.status,
                            text[:200],
                        )

                        if response.status == 200:

                            data = await response.json()

                            self.token = (
                                data.get("token")
                                or data.get("access_token")
                            )

                            if self.token:
                                return

                except Exception as err:

                    _LOGGER.warning(
                        "iDM login test failed %s: %s",
                        path,
                        err,
                    )


        raise Exception(
            "No valid iDM login endpoint found"
        )


    async def get_values(self):
        """Get values from iDM."""

        if not self.token:
            await self.login()

        return {}


        async with aiohttp.ClientSession() as session:

            async with session.get(
                f"{API_URL}/api/installation/{self.installation}",
                headers=headers,
                ssl=False,
            ) as response:

                response.raise_for_status()

                data = await response.json()


                _LOGGER.warning(
                    "iDM API response TEST: %s",
                    data,
                )


                return data