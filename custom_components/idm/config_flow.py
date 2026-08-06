"""Config flow for iDM integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .api import IDMApi
from .const import DOMAIN


class IDMConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a config flow for iDM."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input=None,
    ):
        """Handle user setup."""

        errors = {}

        if user_input is not None:

            try:
                api = IDMApi(
                    username=user_input["username"],
                    password=user_input["password"],
                    installation=user_input["installation"],
                )

                await api.login()

            except Exception:
                errors["base"] = "cannot_connect"

            else:

                await self.async_set_unique_id(
                    f"idm_{user_input['installation']}"
                )

                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="iDM myIDM",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(
                    "username"
                ): str,

                vol.Required(
                    "password"
                ): str,

                vol.Required(
                    "installation"
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )