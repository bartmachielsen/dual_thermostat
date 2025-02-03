import logging
import voluptuous as vol

from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

from homeassistant.components.climate.const import HVACMode, ClimateEntityFeature
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)

DOMAIN = "dual_thermostat"

# Configuration keys for the main and secondary climate devices.
CONF_MAIN_CLIMATE = "main_climate"
CONF_SECONDARY_CLIMATE = "secondary_climate"

# Configuration keys for sensors.
CONF_SENSOR = "sensor"  # Primary indoor sensor.
CONF_OUTDOOR_SENSOR = "outdoor_sensor"  # (Optional) Outdoor sensor.

# Configuration keys for controlling behavior.
CONF_TEMP_THRESHOLD = "temp_threshold"  # Degrees of difference before boosting.
CONF_HEATING_PRESET_TEMPERATURES = "heating_preset_temperatures"  # e.g. {"comfort": 21, "standby": 18, "default": 15}.
CONF_COOLING_PRESET_TEMPERATURES = "cooling_preset_temperatures"  # e.g. {"comfort": 25, "standby": 23, "default": None}.
CONF_MODE_SYNC_TEMPLATE = "mode_sync_template"  # Template to force both devices to run in the same mode.
CONF_OUTDOOR_HOT_THRESHOLD = "outdoor_hot_threshold"  # e.g. 25°C or higher.
CONF_OUTDOOR_COLD_THRESHOLD = "outdoor_cold_threshold"  # e.g. 10°C or lower.

# Default values.
DEFAULT_TEMP_THRESHOLD = 1.0
DEFAULT_HEATING_PRESETS = {"comfort": 21, "standby": 18, "default": 15}
DEFAULT_COOLING_PRESETS = {"comfort": 25, "standby": 23, "default": None}
DEFAULT_OUTDOOR_HOT_THRESHOLD = DEFAULT_COOLING_PRESETS["comfort"]
DEFAULT_OUTDOOR_COLD_THRESHOLD = DEFAULT_HEATING_PRESETS["comfort"]

# Extend the platform schema with our custom configuration.
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAIN_CLIMATE): cv.string,
    vol.Required(CONF_SECONDARY_CLIMATE): cv.string,
    vol.Required(CONF_SENSOR): cv.string,
    vol.Optional(CONF_OUTDOOR_SENSOR): cv.string,
    vol.Optional(CONF_TEMP_THRESHOLD, default=DEFAULT_TEMP_THRESHOLD): vol.Coerce(float),
    vol.Optional(CONF_HEATING_PRESET_TEMPERATURES, default=DEFAULT_HEATING_PRESETS): {cv.string: vol.Coerce(float)},
    vol.Optional(CONF_COOLING_PRESET_TEMPERATURES, default=DEFAULT_COOLING_PRESETS): {cv.string: vol.Coerce(float)},
    vol.Optional(CONF_MODE_SYNC_TEMPLATE): cv.template,
    vol.Optional(CONF_OUTDOOR_HOT_THRESHOLD, default=DEFAULT_OUTDOOR_HOT_THRESHOLD): vol.Coerce(float),
    vol.Optional(CONF_OUTDOOR_COLD_THRESHOLD, default=DEFAULT_OUTDOOR_COLD_THRESHOLD): vol.Coerce(float),
})


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Dual Thermostat platform from a config entry."""
    config = config_entry.data
    await async_setup_platform(hass, config, async_add_entities)
    return True


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Dual Thermostat platform."""
    main_climate = config.get(CONF_MAIN_CLIMATE)
    secondary_climate = config.get(CONF_SECONDARY_CLIMATE)
    sensor = config.get(CONF_SENSOR)
    outdoor_sensor = config.get(CONF_OUTDOOR_SENSOR)
    temp_threshold = config.get(CONF_TEMP_THRESHOLD)
    heating_presets = config.get(CONF_HEATING_PRESET_TEMPERATURES) or DEFAULT_HEATING_PRESETS
    cooling_presets = config.get(CONF_COOLING_PRESET_TEMPERATURES) or DEFAULT_COOLING_PRESETS
    outdoor_hot_threshold = config.get(CONF_OUTDOOR_HOT_THRESHOLD)
    outdoor_cold_threshold = config.get(CONF_OUTDOOR_COLD_THRESHOLD)

    mode_sync_template = config.get(CONF_MODE_SYNC_TEMPLATE)
    if mode_sync_template:
        mode_sync_template = Template(mode_sync_template, hass)

    async_add_entities([
        DualThermostat(
            hass,
            main_climate,
            secondary_climate,
            sensor,
            outdoor_sensor,
            temp_threshold,
            heating_presets,
            cooling_presets,
            mode_sync_template,
            outdoor_hot_threshold,
            outdoor_cold_threshold
        )
    ])


class DualThermostat(ClimateEntity):
    """A dual thermostat that self-manages its subdevices while always reporting 'auto'."""
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.PRESET_MODE
    # The dual thermostat entity always reports 'auto'
    _attr_hvac_modes = [HVACMode.AUTO]

    def __init__(self, hass, main_climate, secondary_climate, sensor, outdoor_sensor,
                 temp_threshold, heating_presets, cooling_presets,
                 mode_sync_template, outdoor_hot_threshold, outdoor_cold_threshold):
        """Initialize the dual thermostat."""
        self.hass = hass
        self._main_climate = main_climate
        self._secondary_climate = secondary_climate
        self._sensor = sensor
        self._outdoor_sensor = outdoor_sensor
        self._temp_threshold = temp_threshold
        self._heating_presets = heating_presets
        self._cooling_presets = cooling_presets
        self._mode_sync_template = mode_sync_template
        self._outdoor_hot_threshold = outdoor_hot_threshold
        self._outdoor_cold_threshold = outdoor_cold_threshold

        self._attr_target_temperature = None
        self._attr_current_temperature = None
        # The dual thermostat always shows AUTO.
        self._attr_hvac_mode = HVACMode.AUTO
        self._attr_preset_mode = "default"

    @property
    def name(self):
        """Return the name of the dual thermostat."""
        return f"Dual Thermostat ({self._main_climate} + {self._secondary_climate})"

    @property
    def current_temperature(self):
        """Return the current indoor temperature."""
        return self._attr_current_temperature

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return self._attr_target_temperature

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        return self._attr_preset_mode

    @property
    def preset_modes(self):
        """Return a list of available preset modes (based on the heating presets)."""
        return list(self._heating_presets.keys())

    def _evaluate_mode_sync(self):
        """If a mode_sync_template is provided, evaluate it to force both devices to the same mode.
        The template should return either 'heat' or 'cool'.
        """
        if self._mode_sync_template is not None:
            try:
                result = self._mode_sync_template.async_render(parse_result=False)
                if result in ["heat", "cool"]:
                    return result
            except Exception as e:
                _LOGGER.error("Error evaluating mode_sync_template: %s", e)
        return None

    @property
    def effective_main_device(self):
        """Return the entity_id of the primary climate device."""
        return self._main_climate

    @property
    def effective_secondary_device(self):
        """Return the entity_id of the secondary climate device."""
        return self._secondary_climate

    async def async_set_temperature(self, **kwargs):
        """Set a new target temperature (manual override)."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        self._attr_target_temperature = temperature
        await self._apply_temperature()
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode):
        """Set a new preset mode and update the target temperature accordingly.
        (The effective HVAC mode for the subdevices is later determined by comparing
        the current indoor temperature with the target.)
        """
        if preset_mode not in self._heating_presets and preset_mode not in self._cooling_presets:
            _LOGGER.error("Preset mode %s not recognized", preset_mode)
            return

        self._attr_preset_mode = preset_mode

        sensor_state = self.hass.states.get(self._sensor)
        current_temp = None
        if sensor_state is not None:
            try:
                current_temp = float(sensor_state.state)
            except Exception as e:
                _LOGGER.error("Error reading sensor %s: %s", self._sensor, e)

        # When both heating and cooling presets exist, choose based on the current temperature.
        if current_temp is not None and preset_mode in self._heating_presets and preset_mode in self._cooling_presets:
            heating_target = self._heating_presets[preset_mode]
            cooling_target = self._cooling_presets[preset_mode]
            midpoint = (heating_target + cooling_target) / 2
            if current_temp < midpoint:
                self._attr_target_temperature = heating_target
            else:
                self._attr_target_temperature = cooling_target
        elif preset_mode in self._heating_presets:
            self._attr_target_temperature = self._heating_presets[preset_mode]
        elif preset_mode in self._cooling_presets:
            self._attr_target_temperature = self._cooling_presets[preset_mode]

        _LOGGER.debug("Preset mode set to %s; Target temp: %s", preset_mode, self._attr_target_temperature)
        await self._apply_temperature()
        self.async_write_ha_state()

    async def _apply_temperature(self):
        """
        Read the current indoor temperature and determine the effective HVAC mode for
        the subdevices (primary and secondary) based on the difference to the target.
        The dual thermostat itself continues to report HVAC mode AUTO.
        """
        sensor_state = self.hass.states.get(self._sensor)
        if sensor_state is None:
            _LOGGER.error("Sensor %s not found", self._sensor)
            return

        try:
            self._attr_current_temperature = float(sensor_state.state)
        except Exception as e:
            _LOGGER.error("Error reading sensor %s: %s", self._sensor, e)
            return

        # Determine the effective mode for subdevices.
        if self._attr_current_temperature < self._attr_target_temperature:
            effective_mode = HVACMode.HEAT
            diff = self._attr_target_temperature - self._attr_current_temperature
        elif self._attr_current_temperature > self._attr_target_temperature:
            effective_mode = HVACMode.COOL
            diff = self._attr_current_temperature - self._attr_target_temperature
        else:
            effective_mode = HVACMode.OFF
            diff = 0

        _LOGGER.debug("Current temp: %s, Target temp: %s, Diff: %s, Effective mode: %s",
                      self._attr_current_temperature, self._attr_target_temperature, diff, effective_mode)

        # Update the primary device with the target temperature and effective HVAC mode.
        await self._set_effective_main_temperature(self._attr_target_temperature)
        await self._set_effective_main_hvac_mode(effective_mode)

        # Activate the secondary device if the temperature difference exceeds the threshold.
        if diff > self._temp_threshold:
            await self._set_effective_secondary(effective_mode)
        else:
            await self._set_effective_secondary(HVACMode.OFF)

        # Optionally, if a mode sync template is provided, enforce that mode.
        desired_mode = self._evaluate_mode_sync()
        if desired_mode:
            sync_mode = HVACMode.COOL if desired_mode == "cool" else HVACMode.HEAT
            await self._set_effective_main_hvac_mode(sync_mode)
            await self._set_effective_secondary(sync_mode)

    async def _set_effective_main_temperature(self, temperature):
        """Call the climate service to set the primary device's temperature."""
        service_data = {
            "entity_id": self.effective_main_device,
            "temperature": temperature,
        }
        _LOGGER.debug("Setting main device %s to temperature %s", self.effective_main_device, temperature)
        await self.hass.services.async_call("climate", "set_temperature", service_data)

    async def _set_effective_main_hvac_mode(self, hvac_mode):
        """Call the climate service to set the primary device's HVAC mode."""
        service_data = {
            "entity_id": self.effective_main_device,
            "hvac_mode": hvac_mode,
        }
        _LOGGER.debug("Setting main device %s to hvac_mode %s", self.effective_main_device, hvac_mode)
        await self.hass.services.async_call("climate", "set_hvac_mode", service_data)

    async def _set_effective_secondary(self, hvac_mode):
        """Call the climate service to set the secondary device's HVAC mode."""
        service_data = {
            "entity_id": self.effective_secondary_device,
            "hvac_mode": hvac_mode,
        }
        _LOGGER.debug("Setting secondary device %s to hvac_mode %s", self.effective_secondary_device, hvac_mode)
        await self.hass.services.async_call("climate", "set_hvac_mode", service_data)

    async def async_update(self):
        """Fetch new state data (update the indoor sensor reading)."""
        sensor_state = self.hass.states.get(self._sensor)
        if sensor_state is not None:
            try:
                self._attr_current_temperature = float(sensor_state.state)
            except Exception as e:
                _LOGGER.error("Error updating sensor %s: %s", self._sensor, e)
