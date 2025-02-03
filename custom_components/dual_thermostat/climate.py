import logging
import voluptuous as vol

from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

from homeassistant.components.climate.const import HVACMode, ClimateEntityFeature
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)

DOMAIN = "dual_thermostat"

# Configuration keys for the main and secondary climate devices
CONF_MAIN_CLIMATE = "main_climate"
CONF_SECONDARY_CLIMATE = "secondary_climate"

# Configuration keys for sensors
CONF_SENSOR = "sensor"  # Primary indoor sensor
CONF_OUTDOOR_SENSOR = "outdoor_sensor"  # Used to decide between heat and cool

# Configuration keys for controlling behavior
CONF_OPERATION_MODE = "operation_mode"  # How to boost the secondary device (always, on_demand, constant_on_demand)
CONF_TEMP_THRESHOLD = "temp_threshold"  # Degrees of difference before boosting
CONF_HEATING_PRESET_TEMPERATURES = "heating_preset_temperatures"  # e.g. {"comfort": 21, "eco": 17}
CONF_COOLING_PRESET_TEMPERATURES = "cooling_preset_temperatures"  # e.g. {"comfort": 25, "eco": 28}
CONF_MODE_SYNC_TEMPLATE = "mode_sync_template"  # Template to force both ACs to run in the same mode

# Keys for smart comfort mode decision
CONF_OUTDOOR_HOT_THRESHOLD = "outdoor_hot_threshold"  # e.g. 25°C or higher means very hot → cool
CONF_OUTDOOR_COLD_THRESHOLD = "outdoor_cold_threshold"  # e.g. 10°C or lower means very cold → heat

# Allowed operation modes.
OPERATION_MODES = ["always", "on_demand", "constant_on_demand"]

# Default values.
DEFAULT_OPERATION_MODE = "on_demand"
DEFAULT_TEMP_THRESHOLD = 1.0
DEFAULT_HEATING_PRESETS = {"comfort": 21, "eco": 17}
DEFAULT_COOLING_PRESETS = {"comfort": 25, "eco": 28}
DEFAULT_OUTDOOR_HOT_THRESHOLD = 25.0
DEFAULT_OUTDOOR_COLD_THRESHOLD = 10.0

# Extend the platform schema with our custom configuration.
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAIN_CLIMATE): cv.string,
    vol.Required(CONF_SECONDARY_CLIMATE): cv.string,
    vol.Required(CONF_SENSOR): cv.string,
    vol.Optional(CONF_OUTDOOR_SENSOR): cv.string,
    vol.Optional(CONF_OPERATION_MODE, default=DEFAULT_OPERATION_MODE): vol.In(OPERATION_MODES),
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
    operation_mode = config.get(CONF_OPERATION_MODE)
    temp_threshold = config.get(CONF_TEMP_THRESHOLD)
    heating_presets = config.get(CONF_HEATING_PRESET_TEMPERATURES)
    cooling_presets = config.get(CONF_COOLING_PRESET_TEMPERATURES)
    outdoor_hot_threshold = config.get(CONF_OUTDOOR_HOT_THRESHOLD)
    outdoor_cold_threshold = config.get(CONF_OUTDOOR_COLD_THRESHOLD)

    mode_sync_template = config.get(CONF_MODE_SYNC_TEMPLATE)
    if mode_sync_template:
        # Convert the template string into a Template object.
        mode_sync_template = Template(mode_sync_template, hass)

    async_add_entities([
        DualThermostat(
            hass,
            main_climate,
            secondary_climate,
            sensor,
            outdoor_sensor,
            operation_mode,
            temp_threshold,
            heating_presets,
            cooling_presets,
            mode_sync_template,
            outdoor_hot_threshold,
            outdoor_cold_threshold
        )
    ])


class DualThermostat(ClimateEntity):
    """Representation of a dual thermostat that automatically chooses between heating and cooling."""
    # Use the new attribute naming conventions.
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]

    def __init__(self, hass, main_climate, secondary_climate, sensor, outdoor_sensor,
                 operation_mode, temp_threshold, heating_presets, cooling_presets,
                 mode_sync_template, outdoor_hot_threshold, outdoor_cold_threshold):
        """Initialize the dual thermostat."""
        self.hass = hass
        self._main_climate = main_climate
        self._secondary_climate = secondary_climate
        self._sensor = sensor
        self._outdoor_sensor = outdoor_sensor
        self._operation_mode = operation_mode
        self._temp_threshold = temp_threshold
        self._heating_presets = heating_presets
        self._cooling_presets = cooling_presets
        self._mode_sync_template = mode_sync_template
        self._outdoor_hot_threshold = outdoor_hot_threshold
        self._outdoor_cold_threshold = outdoor_cold_threshold

        # Use Home Assistant’s attribute names so that state reporting works out of the box.
        self._attr_target_temperature = None
        self._attr_current_temperature = None
        self._attr_hvac_mode = HVACMode.OFF  # Start off.
        self._attr_preset_mode = "comfort"  # Default preset

    @property
    def name(self):
        """Return the name of the entity."""
        return f"Dual Thermostat ({self._main_climate} + {self._secondary_climate})"

    @property
    def current_temperature(self):
        """Return the current indoor temperature from the primary sensor."""
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
        """Return a list of available preset modes.
        (We assume that the same preset names apply for both heating and cooling.)
        """
        return list(self._heating_presets.keys())

    def _evaluate_mode_sync(self):
        """Evaluate the mode_sync_template, if provided, to force both devices to the same mode.
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
        """Return the entity_id of the effective main device."""
        return self._main_climate

    @property
    def effective_secondary_device(self):
        """Return the entity_id of the effective secondary device."""
        return self._secondary_climate

    async def async_set_temperature(self, **kwargs):
        """Set a new target temperature (manual override)."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        self._attr_target_temperature = temperature

        # Try to match one of our presets.
        for preset, temp in self._heating_presets.items():
            if abs(temp - temperature) < 0.1:
                self._attr_preset_mode = preset
                self._attr_hvac_mode = HVACMode.HEAT
                break

        for preset, temp in self._cooling_presets.items():
            if abs(temp - temperature) < 0.1:
                self._attr_preset_mode = preset
                self._attr_hvac_mode = HVACMode.COOL
                break

        await self._apply_temperature()
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set a new HVAC mode."""
        self._attr_hvac_mode = hvac_mode
        await self._apply_temperature()
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode):
        """Set a new preset mode and update the target temperature accordingly.
        For the 'comfort' preset, the outdoor sensor is used to decide between heat and cool.
        """
        if preset_mode not in self._heating_presets:
            _LOGGER.error("Preset mode %s not recognized", preset_mode)
            return

        self._attr_preset_mode = preset_mode

        if preset_mode == "comfort" and self._outdoor_sensor is not None:
            outdoor_state = self.hass.states.get(self._outdoor_sensor)
            if outdoor_state is not None:
                try:
                    outdoor_temp = float(outdoor_state.state)
                except Exception as e:
                    _LOGGER.error("Error reading outdoor sensor %s: %s", self._outdoor_sensor, e)
                    outdoor_temp = None
            else:
                _LOGGER.error("Outdoor sensor %s not found", self._outdoor_sensor)
                outdoor_temp = None

            if outdoor_temp is not None:
                # If it's very hot outside, choose cooling; if very cold, choose heating.
                if outdoor_temp >= self._outdoor_hot_threshold:
                    self._attr_hvac_mode = HVACMode.COOL
                    self._attr_target_temperature = self._cooling_presets.get(preset_mode, self._attr_target_temperature)
                elif outdoor_temp <= self._outdoor_cold_threshold:
                    self._attr_hvac_mode = HVACMode.HEAT
                    self._attr_target_temperature = self._heating_presets.get(preset_mode, self._attr_target_temperature)
                else:
                    # In between, default to heating (adjustable as needed).
                    self._attr_hvac_mode = HVACMode.HEAT
                    self._attr_target_temperature = self._heating_presets.get(preset_mode, self._attr_target_temperature)
            else:
                # Fall back to heating if outdoor sensor reading fails.
                self._attr_hvac_mode = HVACMode.HEAT
                self._attr_target_temperature = self._heating_presets.get(preset_mode, self._attr_target_temperature)
        else:
            # For non-"comfort" presets, check which mapping contains the preset.
            if preset_mode in self._cooling_presets:
                self._attr_hvac_mode = HVACMode.COOL
                self._attr_target_temperature = self._cooling_presets[preset_mode]
            elif preset_mode in self._heating_presets:
                self._attr_hvac_mode = HVACMode.HEAT
                self._attr_target_temperature = self._heating_presets[preset_mode]

        _LOGGER.debug("Preset mode set to %s; HVAC mode: %s; Target temp: %s",
                      preset_mode, self._attr_hvac_mode, self._attr_target_temperature)
        await self._apply_temperature()
        self.async_write_ha_state()

    async def _apply_temperature(self):
        """
        Apply the target temperature to the effective main device and determine if
        the effective secondary device should be activated.
        For heating: secondary is activated if indoor temperature is below target by more than the threshold.
        For cooling: secondary is activated if indoor temperature is above target by more than the threshold.
        """
        sensor_state = self.hass.states.get(self._sensor)
        if sensor_state is None:
            _LOGGER.error("Sensor %s not found", self._sensor)
            return

        try:
            self._attr_current_temperature = float(sensor_state.state)
        except Exception as e:
            _LOGGER.error("Error reading state from sensor %s: %s", self._sensor, e)
            return

        # Calculate the difference between indoor temperature and target.
        if self._attr_hvac_mode == HVACMode.COOL:
            diff = self._attr_current_temperature - self._attr_target_temperature
        else:
            diff = self._attr_target_temperature - self._attr_current_temperature

        _LOGGER.debug("Indoor sensor current temp: %s, Target: %s, Diff: %s, Mode: %s",
                      self._attr_current_temperature, self._attr_target_temperature, diff, self._attr_hvac_mode)

        # Decide whether to boost with the secondary device.
        if diff > self._temp_threshold:
            if self._operation_mode == "always":
                await self._set_effective_secondary(self._attr_hvac_mode)
            elif self._operation_mode == "on_demand":
                if diff > (self._temp_threshold + 1.0):
                    await self._set_effective_secondary(self._attr_hvac_mode)
                else:
                    await self._set_effective_secondary(HVACMode.OFF)
            elif self._operation_mode == "constant_on_demand":
                await self._set_effective_secondary(self._attr_hvac_mode)
        else:
            await self._set_effective_secondary(HVACMode.OFF)

        # Always update the effective main device with the target temperature.
        await self._set_effective_main_temperature(self._attr_target_temperature)

        # If a mode sync template is provided, enforce the same HVAC mode on both devices.
        desired_mode = self._evaluate_mode_sync()
        if desired_mode:
            self._attr_hvac_mode = HVACMode.COOL if desired_mode == "cool" else HVACMode.HEAT
            await self._set_effective_main_hvac_mode(self._attr_hvac_mode)
            await self._set_effective_secondary(self._attr_hvac_mode)

    async def _set_effective_main_temperature(self, temperature):
        """Call the climate service to set the effective main device's temperature."""
        service_data = {
            "entity_id": self.effective_main_device,
            "temperature": temperature,
        }
        _LOGGER.debug("Setting effective main climate %s to %s", self.effective_main_device, temperature)
        await self.hass.services.async_call("climate", "set_temperature", service_data)

    async def _set_effective_main_hvac_mode(self, hvac_mode):
        """Call the climate service to set the effective main device's HVAC mode."""
        service_data = {
            "entity_id": self.effective_main_device,
            "hvac_mode": hvac_mode,
        }
        _LOGGER.debug("Setting effective main climate %s to hvac_mode %s", self.effective_main_device, hvac_mode)
        await self.hass.services.async_call("climate", "set_hvac_mode", service_data)

    async def _set_effective_secondary(self, hvac_mode):
        """Call the climate service to set the effective secondary device's HVAC mode."""
        service_data = {
            "entity_id": self.effective_secondary_device,
            "hvac_mode": hvac_mode,
        }
        _LOGGER.debug("Setting effective secondary climate %s to hvac_mode %s", self.effective_secondary_device, hvac_mode)
        await self.hass.services.async_call("climate", "set_hvac_mode", service_data)

    async def async_update(self):
        """Fetch new state data for the dual thermostat (update the indoor sensor reading)."""
        sensor_state = self.hass.states.get(self._sensor)
        if sensor_state is not None:
            try:
                self._attr_current_temperature = float(sensor_state.state)
            except Exception as e:
                _LOGGER.error("Error updating current_temperature from sensor %s: %s", self._sensor, e)
