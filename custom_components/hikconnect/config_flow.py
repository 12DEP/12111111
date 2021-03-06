import logging

import voluptuous as vol
from hikconnect.api import HikConnect
from hikconnect.exceptions import LoginError
from homeassistant import config_entries, core

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_schema = {
    vol.Required("username"): str,
    vol.Required("password"): str,
}
DATA_SCHEMA = vol.Schema(_schema)


async def validate_input(hass: core.HomeAssistant, data: dict):
    """
    Validate the user input by logging into Hik-Connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    async with HikConnect() as api:
        await api.login(data["username"], data["password"])


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step of config flow initiated by user manually."""
        errors = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
                unique_id = user_input["username"]
                _LOGGER.info(
                    "Adding Hik-Connect config entry with unique_id=%s", unique_id
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=unique_id, data=user_input)
            except LoginError as e:
                # to show hikconnect library exception in logs
                _LOGGER.exception("Hik-Connect login failed")
                errors["base"] = "login_failed"
            except Exception:  # NOQA
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
