import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from .const import (
    DOMAIN,
    CONF_MAIN_CLIMATE,
    CONF_SECONDARY_CLIMATE,
    CONF_SENSOR,
    CONF_OUTDOOR_SENSOR,
    CONF_TEMP_THRESHOLD_PRIMARY,
    CONF_TEMP_THRESHOLD_SECONDARY,
    CONF_OUTDOOR_HOT_THRESHOLD,
    CONF_PRIMARY_OFFSET,
    CONF_SECONDARY_OFFSET,
    CONF_HEATING_PRESETS,
    CONF_COOLING_PRESETS,
    DEFAULT_TEMP_THRESHOLD_PRIMARY,
    DEFAULT_TEMP_THRESHOLD_SECONDARY,
    DEFAULT_OUTDOOR_HOT_THRESHOLD,
    DEFAULT_PRIMARY_OFFSET,
    DEFAULT_SECONDARY_OFFSET,
    DEFAULT_HEATING_PRESETS,
    DEFAULT_COOLING_PRESETS,
)

def dict_to_raw_str(d: dict) -> str:
    """Convert a dictionary into a raw string in key:value, comma-separated format."""
    return ", ".join(f"{k}:{v}" for k, v in d.items())

def parse_presets(raw: str) -> dict:
    """Parse a raw string of key:value pairs into a dictionary."""
    result = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        try:
            # Convert to float if possible.
            result[key.strip()] = float(value.strip())
        except ValueError:
            result[key.strip()] = value.strip()
    return result


class SmartClimateOptionsFlow(config_entries.OptionsFlow):
    """Handle a simplified options flow for the Smart Climate integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        """Manage the options flow."""
        if user_input is not None:
            # Parse the raw strings into dictionaries.
            heating_raw = user_input.get("heating_presets", "")
            cooling_raw = user_input.get("cooling_presets", "")
            user_input[CONF_HEATING_PRESETS] = parse_presets(heating_raw)
            user_input[CONF_COOLING_PRESETS] = parse_presets(cooling_raw)
            # Remove the raw string keys.
            user_input.pop("heating_presets", None)
            user_input.pop("cooling_presets", None)
            return self.async_create_entry(data=user_input)

        base_schema = {
            vol.Optional(
                CONF_MAIN_CLIMATE,
                default=self.config_entry.data.get(CONF_MAIN_CLIMATE)
            ): cv.entity_id,
            vol.Optional(
                CONF_SECONDARY_CLIMATE,
                default=self.config_entry.data.get(CONF_SECONDARY_CLIMATE)
            ): cv.entity_id,
            vol.Optional(
                CONF_SENSOR,
                default=self.config_entry.data.get(CONF_SENSOR)
            ): cv.entity_id,
            vol.Optional(
                CONF_OUTDOOR_SENSOR,
                default=self.config_entry.data.get(CONF_OUTDOOR_SENSOR, "")
            ): cv.entity_id,
            vol.Optional(
                CONF_TEMP_THRESHOLD_PRIMARY,
                default=self.config_entry.data.get(CONF_TEMP_THRESHOLD_PRIMARY, DEFAULT_TEMP_THRESHOLD_PRIMARY)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_TEMP_THRESHOLD_SECONDARY,
                default=self.config_entry.data.get(CONF_TEMP_THRESHOLD_SECONDARY, DEFAULT_TEMP_THRESHOLD_SECONDARY)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_OUTDOOR_HOT_THRESHOLD,
                default=self.config_entry.data.get(CONF_OUTDOOR_HOT_THRESHOLD, DEFAULT_OUTDOOR_HOT_THRESHOLD)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_PRIMARY_OFFSET,
                default=self.config_entry.data.get(CONF_PRIMARY_OFFSET, DEFAULT_PRIMARY_OFFSET)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_SECONDARY_OFFSET,
                default=self.config_entry.data.get(CONF_SECONDARY_OFFSET, DEFAULT_SECONDARY_OFFSET)
            ): vol.Coerce(float),
            # Provide raw string inputs for the presets.
            vol.Optional(
                CONF_HEATING_PRESETS,
                default=dict_to_raw_str(self.config_entry.data.get(CONF_HEATING_PRESETS, DEFAULT_HEATING_PRESETS))
            ): str,
            vol.Optional(
                CONF_COOLING_PRESETS,
                default=dict_to_raw_str(self.config_entry.data.get(CONF_COOLING_PRESETS, DEFAULT_COOLING_PRESETS))
            ): str,
        }
        return self.async_show_form(step_id="init", data_schema=vol.Schema(base_schema))