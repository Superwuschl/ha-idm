from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, NAME


class IDMConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Config Flow für die iDM Modbus / myIDM Integration."""

    VERSION = 2

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ):
        """Konfigurationsschritt für die erstmalige Einrichtung."""

        if user_input is not None:
            data = {
                # ==================================================
                # MODBUS
                # ==================================================

                "modbus_host": user_input["modbus_host"],
                "modbus_port": int(user_input["modbus_port"]),
                "modbus_device_id": int(
                    user_input["modbus_device_id"]
                ),
                "modbus_timeout": float(
                    user_input["modbus_timeout"]
                ),

                # ==================================================
                # iDM / myIDM
                # ==================================================

                "wp_id": int(user_input["wp_id"]),
            }

            access_token = user_input.get("access_token")

            if access_token:
                data["access_token"] = access_token

            return self.async_create_entry(
                title=NAME,
                data=data,
            )

        schema = vol.Schema(
            {
                # --------------------------------------------------
                # MODBUS
                # --------------------------------------------------

                vol.Required(
                    "modbus_host",
                    default="192.168.30.188",
                ): str,

                vol.Required(
                    "modbus_port",
                    default=502,
                ): int,

                vol.Required(
                    "modbus_device_id",
                    default=1,
                ): int,

                vol.Required(
                    "modbus_timeout",
                    default=2.0,
                ): vol.Coerce(float),

                # --------------------------------------------------
                # iDM / myIDM
                # --------------------------------------------------

                vol.Required(
                    "wp_id",
                    default=3419,
                ): int,

                vol.Optional(
                    "access_token",
                    default="",
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    # ==============================================================
    # OPTIONS FLOW
    # ==============================================================

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Erzeugt den Optionen-Dialog."""

        return IDMOptionsFlow()


class IDMOptionsFlow(
    config_entries.OptionsFlow,
):
    """Optionen für eine bestehende iDM Config Entry."""

    async def async_step_init(
        self,
        user_input: dict | None = None,
    ):
        """myIDM Access Token konfigurieren."""

        if user_input is not None:
            access_token = user_input.get(
                "access_token",
                "",
            ).strip()

            data = {}

            if access_token:
                data["access_token"] = access_token

            return self.async_create_entry(
                title="",
                data=data,
            )

        # ==========================================================
        # Vorhandenen Token nur als ausgefüllt darstellen.
        #
        # Der echte Token wird NICHT als Default in das Formular
        # geschrieben, damit er nicht unnötig sichtbar ist.
        # ==========================================================

        current_token = self.config_entry.options.get(
            "access_token"
        )

        if not current_token:
            current_token = self.config_entry.data.get(
                "access_token"
            )

        schema = vol.Schema(
            {
                vol.Optional(
                    "access_token",
                    default="",
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )