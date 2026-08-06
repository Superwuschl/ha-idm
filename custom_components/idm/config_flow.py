from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN, NAME


class IDMConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):

    VERSION = 1


    async def async_step_user(
        self,
        user_input=None,
    ):

        if user_input:

            return self.async_create_entry(
                title=NAME,
                data={
                    "access_token":
                        user_input["access_token"],

                    "refresh_token":
                        user_input["refresh_token"],

                    "wp_id":
                        int(
                            user_input["wp_id"]
                        ),
                },
            )


        schema = vol.Schema(
            {
                vol.Required(
                    "access_token"
                ): str,

                vol.Required(
                    "refresh_token"
                ): str,

                vol.Required(
                    "wp_id",
                    default=3419,
                ): int,
            }
        )


        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )
