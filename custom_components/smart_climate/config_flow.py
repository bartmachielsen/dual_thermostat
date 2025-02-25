import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.helpers.selector import selector
from homeassistant.core import callback
from .const import (
    DOMAIN,
    CONF_MAIN_CLIMATE,
    CONF_SECONDARY_CLIMATE,
    CONF_SENSOR,
    CONF_OUTDOOR_SENSOR,
    CONF_TEMP_THRESHOLD_PRIMARY,
    CONF_TEMP_THRESHOLD_SECONDARY,
    CONF_OUTDOOR_HOT_THRESHOLD,
)
from .options_flow import SmartClimateOptionsFlow  # noqa

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_MAIN_CLIMATE): selector({"entity": {"domain": "climate"}}),
    vol.Optional(CONF_SECONDARY_CLIMATE): selector({"entity": {"domain": "climate"}}),
    vol.Required(CONF_SENSOR): selector({"entity": {"domain": ["sensor"]}}),
    vol.Optional(CONF_OUTDOOR_SENSOR): selector({"entity": {"domain": ["sensor"]}}),
    vol.Optional(CONF_TEMP_THRESHOLD_PRIMARY, default=1): vol.Coerce(float),
    vol.Optional(CONF_TEMP_THRESHOLD_SECONDARY, default=3): vol.Coerce(float),
    vol.Optional(CONF_OUTDOOR_HOT_THRESHOLD, default=25.0): vol.Coerce(float),
})


class SmartClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Smart Climate integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Smart Climate", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_import(self, user_input: dict) -> dict:
        """Import configuration from YAML if present."""
        return await self.async_step_user(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow for Smart Climate."""
        return SmartClimateOptionsFlow(config_entry)


async def async_get_options_flow(
    config_entry: config_entries.ConfigEntry,
) -> config_entries.OptionsFlow:
    """Get the options flow for Smart Climate."""
    return SmartClimateOptionsFlow(config_entry)
