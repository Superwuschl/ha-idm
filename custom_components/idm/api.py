"""API client for iDM myIDM."""

import hashlib
import aiohttp

from .const import API_URL


class IDMApi:
    """Client for the iDM myIDM API."""

    def __init__(self, username: str, password: str):
        """Initialize API client."""
        self.username = username
        self.password = password
        self.token = None
        self.installation = None


    async def login(self) -> bool:
        """Login to myIDM and get token."""

        password_hash = hashlib.sha1(
            self.password.encode("utf-8")
        ).hexdigest()

        async with aiohttp.ClientSession(
            headers={
                "User-Agent": "IDM App (iOS)"
            }
        ) as session:

            async with session.post(
                f"{API_URL}/api/user/login",
                data={
                    "username": self.username,
                    "password": password_hash,
                },
                ssl=False,
            ) as response:

                data = await response.json()

                self.token = data.get("token")

                installations = data.get("installations", [])

                if installations:
                    self.installation = installations[0]["id"]

                return self.token is not None


    async def get_values(self) -> dict:
        """Read current values from heat pump."""

        if not self.token or not self.installation:
            raise Exception("Not logged in")

        async with aiohttp.ClientSession(
            headers={
                "User-Agent": "IDM App (iOS)"
            }
        ) as session:

            async with session.post(
                f"{API_URL}/api/installation/values",
                data={
                    "token": self.token,
                    "installation": self.installation,
                },
                ssl=False,
            ) as response:

                return await response.json()