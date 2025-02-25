import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import selector
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


class SmartClimateOptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for Smart Climate using the official documentation style."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        """Manage the options flow."""
        if user_input is not None:
            # Convert dynamic preset fields into proper preset dictionaries.
            heating_presets = {}
            cooling_presets = {}
            keys_to_remove = []
            for key, value in user_input.items():
                if key.startswith("heating_"):
                    preset = key[len("heating_"):]
                    heating_presets[preset] = value
                    keys_to_remove.append(key)
                elif key.startswith("cooling_"):
                    preset = key[len("cooling_"):]
                    cooling_presets[preset] = value
                    keys_to_remove.append(key)
            # Remove the individual preset keys from the user input.
            for key in keys_to_remove:
                user_input.pop(key)
            # Save the rebuilt presets in the options data.
            user_input[CONF_HEATING_PRESETS] = heating_presets
            user_input[CONF_COOLING_PRESETS] = cooling_presets

            return self.async_create_entry(data=user_input)

        # Build the base schema.
        base_schema = {
            vol.Optional(
                CONF_MAIN_CLIMATE,
                default=self.config_entry.data.get(CONF_MAIN_CLIMATE),
            ): selector({"entity": {"domain": "climate"}}),
            vol.Optional(
                CONF_SECONDARY_CLIMATE,
                default=self.config_entry.data.get(CONF_SECONDARY_CLIMATE),
            ): selector({"entity": {"domain": "climate"}}),
            vol.Optional(
                CONF_SENSOR,
                default=self.config_entry.data.get(CONF_SENSOR),
            ): selector({"entity": {"domain": "sensor"}}),
            vol.Optional(
                CONF_OUTDOOR_SENSOR,
                default=self.config_entry.data.get(CONF_OUTDOOR_SENSOR, ""),
            ): selector({"entity": {"domain": "sensor"}}),
            vol.Optional(
                CONF_TEMP_THRESHOLD_PRIMARY,
                default=self.config_entry.data.get(
                    CONF_TEMP_THRESHOLD_PRIMARY, DEFAULT_TEMP_THRESHOLD_PRIMARY
                ),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_TEMP_THRESHOLD_SECONDARY,
                default=self.config_entry.data.get(
                    CONF_TEMP_THRESHOLD_SECONDARY, DEFAULT_TEMP_THRESHOLD_SECONDARY
                ),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_OUTDOOR_HOT_THRESHOLD,
                default=self.config_entry.data.get(
                    CONF_OUTDOOR_HOT_THRESHOLD, DEFAULT_OUTDOOR_HOT_THRESHOLD
                ),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_PRIMARY_OFFSET,
                default=self.config_entry.data.get(CONF_PRIMARY_OFFSET, DEFAULT_PRIMARY_OFFSET),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_SECONDARY_OFFSET,
                default=self.config_entry.data.get(CONF_SECONDARY_OFFSET, DEFAULT_SECONDARY_OFFSET),
            ): vol.Coerce(float),
        }

        # Dynamically add fields for heating presets.
        current_heating_presets = self.config_entry.data.get(CONF_HEATING_PRESETS, DEFAULT_HEATING_PRESETS)
        for preset, default_temp in current_heating_presets.items():
            key = f"heating_{preset}"
            base_schema[key] = vol.Optional(key, default=default_temp)

        # Dynamically add fields for cooling presets.
        current_cooling_presets = self.config_entry.data.get(CONF_COOLING_PRESETS, DEFAULT_COOLING_PRESETS)
        for preset, default_temp in current_cooling_presets.items():
            key = f"cooling_{preset}"
            base_schema[key] = vol.Optional(key, default=default_temp)

        options_schema = vol.Schema(base_schema)
        # Merge any suggested values from entry.options (if present).
        merged_schema = self.add_suggested_values_to_schema(
            options_schema, self.config_entry.options
        )
        return self.async_show_form(step_id="init", data_schema=merged_schema)
