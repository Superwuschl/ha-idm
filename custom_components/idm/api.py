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


    async def login(self):

        """Test iDM login endpoints."""

        endpoints = [
            "/api/user/login",
            "/api/auth/login",
            "/api/login",
            "/api/v1/login",
            "/api/account/login",
            "/rest/login",
        ]


        async with aiohttp.ClientSession() as session:

            for endpoint in endpoints:

                url = f"{API_URL}{endpoint}"

                try:

                    async with session.post(
                        url,
                        json={
                            "username": self.username,
                            "password": self.password,
                        },
                        ssl=False,
                    ) as response:

                        body = await response.text()


                        _LOGGER.warning(
                            "iDM TEST %s -> %s : %s",
                            endpoint,
                            response.status,
                            body[:500],
                        )


                except Exception as err:

                    _LOGGER.warning(
                        "iDM TEST %s ERROR: %s",
                        endpoint,
                        err,
                    )


        raise Exception(
            "iDM API endpoint detection finished - check logs"
        )


    async def get_values(self):

        """Get values."""

        return {}