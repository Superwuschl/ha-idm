"""Config flow for iDM integration."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class IDMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iDM."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle user setup."""

        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title="iDM myIDM",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required("username"): str,
                vol.Required("password"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )