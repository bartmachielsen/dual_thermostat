import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.helpers.selector import selector

DOMAIN = "dual_thermostat"

_LOGGER = logging.getLogger(__name__)

# Configuration keys.
CONF_MAIN_CLIMATE = "main_climate"
CONF_SECONDARY_CLIMATE = "secondary_climate"
CONF_SENSOR = "sensor"
CONF_OUTDOOR_SENSOR = "outdoor_sensor"
CONF_TEMP_THRESHOLD = "temp_threshold"

# These keys are used for user input and then consolidated.
CONF_HEATING_COMFORT_TEMPERATURE = "heating_comfort_temperature"
CONF_HEATING_ECO_TEMPERATURE = "heating_eco_temperature"
CONF_COOLING_COMFORT_TEMPERATURE = "cooling_comfort_temperature"
CONF_COOLING_ECO_TEMPERATURE = "cooling_eco_temperature"

# Final keys passed to the integration.
CONF_HEATING_PRESET_TEMPERATURES = "heating_preset_temperatures"
CONF_COOLING_PRESET_TEMPERATURES = "cooling_preset_temperatures"

CONF_OUTDOOR_HOT_THRESHOLD = "outdoor_hot_threshold"
CONF_OUTDOOR_COLD_THRESHOLD = "outdoor_cold_threshold"
CONF_MODE_SYNC_TEMPLATE = "mode_sync_template"
CONF_MIN_RUNTIME = "min_runtime_seconds"

# Schema for initial config flow.
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_MAIN_CLIMATE): selector({"entity": {"domain": "climate"}}),
    vol.Required(CONF_SECONDARY_CLIMATE): selector({"entity": {"domain": "climate"}}),
    vol.Required(CONF_SENSOR): selector({"entity": {"domain": ["sensor"]}}),
    vol.Optional(CONF_OUTDOOR_SENSOR): selector({"entity": {"domain": ["sensor"]}}),
    vol.Optional(CONF_TEMP_THRESHOLD, default=1.5): vol.Coerce(float),
    vol.Optional(CONF_HEATING_COMFORT_TEMPERATURE, default=21): vol.Coerce(float),
    vol.Optional(CONF_HEATING_ECO_TEMPERATURE, default=17): vol.Coerce(float),
    vol.Optional(CONF_COOLING_COMFORT_TEMPERATURE, default=25): vol.Coerce(float),
    vol.Optional(CONF_COOLING_ECO_TEMPERATURE, default=28): vol.Coerce(float),
    vol.Optional(CONF_OUTDOOR_HOT_THRESHOLD, default=25.0): vol.Coerce(float),
    vol.Optional(CONF_OUTDOOR_COLD_THRESHOLD, default=10.0): vol.Coerce(float),
    vol.Optional(CONF_MODE_SYNC_TEMPLATE, default=""): str,
    vol.Optional(CONF_MIN_RUNTIME, default=300): vol.Coerce(int),
})


class DualThermostatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Dual Thermostat integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Consolidate heating preset temperatures into a dictionary.
            heating_preset = {
                "comfort": user_input.pop(CONF_HEATING_COMFORT_TEMPERATURE),
                "eco": user_input.pop(CONF_HEATING_ECO_TEMPERATURE),
            }
            # Consolidate cooling preset temperatures into a dictionary.
            cooling_preset = {
                "comfort": user_input.pop(CONF_COOLING_COMFORT_TEMPERATURE),
                "eco": user_input.pop(CONF_COOLING_ECO_TEMPERATURE),
            }
            user_input[CONF_HEATING_PRESET_TEMPERATURES] = heating_preset
            user_input[CONF_COOLING_PRESET_TEMPERATURES] = cooling_preset

            return self.async_create_entry(title="Dual Thermostat", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, user_input):
        """Import configuration from YAML if present."""
        return await self.async_step_user(user_input)


class DualThermostatOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Dual Thermostat."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Consolidate preset temperatures from options.
            heating_preset = {
                "comfort": user_input.pop(CONF_HEATING_COMFORT_TEMPERATURE),
                "eco": user_input.pop(CONF_HEATING_ECO_TEMPERATURE),
            }
            cooling_preset = {
                "comfort": user_input.pop(CONF_COOLING_COMFORT_TEMPERATURE),
                "eco": user_input.pop(CONF_COOLING_ECO_TEMPERATURE),
            }
            user_input[CONF_HEATING_PRESET_TEMPERATURES] = heating_preset
            user_input[CONF_COOLING_PRESET_TEMPERATURES] = cooling_preset

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
                CONF_TEMP_THRESHOLD,
                default=self.config_entry.data.get(CONF_TEMP_THRESHOLD, 1.5)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_HEATING_COMFORT_TEMPERATURE,
                default=self.config_entry.data.get(CONF_HEATING_PRESET_TEMPERATURES, {}).get("comfort", 21)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_HEATING_ECO_TEMPERATURE,
                default=self.config_entry.data.get(CONF_HEATING_PRESET_TEMPERATURES, {}).get("eco", 17)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_COOLING_COMFORT_TEMPERATURE,
                default=self.config_entry.data.get(CONF_COOLING_PRESET_TEMPERATURES, {}).get("comfort", 25)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_COOLING_ECO_TEMPERATURE,
                default=self.config_entry.data.get(CONF_COOLING_PRESET_TEMPERATURES, {}).get("eco", 28)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_OUTDOOR_HOT_THRESHOLD,
                default=self.config_entry.data.get(CONF_OUTDOOR_HOT_THRESHOLD, 25.0)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_OUTDOOR_COLD_THRESHOLD,
                default=self.config_entry.data.get(CONF_OUTDOOR_COLD_THRESHOLD, 10.0)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_MODE_SYNC_TEMPLATE,
                default=self.config_entry.data.get(CONF_MODE_SYNC_TEMPLATE, "")
            ): str,
            vol.Optional(
                CONF_MIN_RUNTIME,
                default=self.config_entry.data.get(CONF_MIN_RUNTIME, 300)
            ): vol.Coerce(int),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)


async def async_get_options_flow(config_entry):
    """Get the options flow for Dual Thermostat."""
    return DualThermostatOptionsFlow(config_entry)
