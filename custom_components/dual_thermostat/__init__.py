"""Initialize the Dual Thermostat integration."""
DOMAIN = "dual_thermostat"

async def async_setup(hass, config):
    """Set up the Dual Thermostat component."""
    # If you have any global setup, do it here.
    return True

async def async_setup_entry(hass, entry):
    """Set up Dual Thermostat from a config entry."""
    # Forward the entry setup to the climate platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "climate")
    )
    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "climate")
    return unload_ok
