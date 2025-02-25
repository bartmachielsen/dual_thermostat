import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.helpers.selector import selector
from .const import *

_LOGGER = logging.getLogger(__name__)

# Schema for initial config flow.
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

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Smart Climate", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, user_input):
        """Import configuration from YAML if present."""
        return await self.async_step_user(user_input)


class SmartClimateOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Smart Climate."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Optional(
                CONF_MAIN_CLIMATE,
                default=self.config_entry.data.get(CONF_MAIN_CLIMATE)
            ): selector({"entity": {"domain": "climate"}}),
            vol.Optional(
                CONF_SECONDARY_CLIMATE,
                default=self.config_entry.data.get(CONF_SECONDARY_CLIMATE)
            ): selector({"entity": {"domain": "climate"}}),
            vol.Optional(
                CONF_SENSOR,
                default=self.config_entry.data.get(CONF_SENSOR)
            ): selector({"entity": {"domain": ["sensor"]}}),
            vol.Optional(
                CONF_OUTDOOR_SENSOR,
                default=self.config_entry.data.get(CONF_OUTDOOR_SENSOR, "")
            ): selector({"entity": {"domain": ["sensor"]}}),
            vol.Optional(
                CONF_TEMP_THRESHOLD_PRIMARY,
                default=self.config_entry.data.get(CONF_TEMP_THRESHOLD_PRIMARY)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_TEMP_THRESHOLD_SECONDARY,
                default=self.config_entry.data.get(CONF_TEMP_THRESHOLD_SECONDARY)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_OUTDOOR_HOT_THRESHOLD,
                default=self.config_entry.data.get(CONF_OUTDOOR_HOT_THRESHOLD, 25.0)
            ): vol.Coerce(float),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)


async def async_get_options_flow(config_entry):
    """Get the options flow for Smart Climate."""
    return SmartClimateOptionsFlow(config_entry)
