"""API client for the iDM myIDM cloud."""

from __future__ import annotations

import hashlib
import logging

import aiohttp

from .const import API_URL

_LOGGER = logging.getLogger(__name__)


class IDMApi:
    """API client for iDM myIDM."""

    def __init__(
        self,
        username: str,
        password: str,
        installation: str,
    ) -> None:
        """Initialize API."""

        self._username = username
        self._password = password
        self._installation = installation

        self._token: str | None = None

    async def login(self) -> None:
        """Login to myIDM."""

        password_hash = hashlib.sha1(
            self._password.encode("utf-8")
        ).hexdigest()

        async with aiohttp.ClientSession(
            headers={
                "User-Agent": "IDM App (iOS)"
            }
        ) as session:

            async with session.post(
                f"{API_URL}/api/user/login",
                data={
                    "username": self._username,
                    "password": password_hash,
                },
                ssl=False,
            ) as response:

                response.raise_for_status()

                data = await response.json()

                token = data.get("token")

                if not token:
                    raise RuntimeError("Login failed")

                self._token = token

    async def get_values(self) -> dict:
        """Return installation values."""

        if self._token is None:
            await self.login()

        async with aiohttp.ClientSession(
            headers={
                "User-Agent": "IDM App (iOS)"
            }
        ) as session:

            async with session.post(
                f"{API_URL}/api/installation/values",
                data={
                    "token": self._token,
                    "installation": self._installation,
                },
                ssl=False,
            ) as response:

                response.raise_for_status()

                return await response.json()