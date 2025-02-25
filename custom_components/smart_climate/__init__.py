"""Initialize the Dual Thermostat integration."""

DOMAIN = "smart_climate"


async def async_setup(hass, config):
    """Set up the Smart Thermostat component."""
    # Global setup (if needed)
    return True


async def async_setup_entry(hass, entry):
    """Set up Smart Climate from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    result = await hass.config_entries.async_forward_entry_setups(entry, ["climate"])
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    try:
        unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "climate")
    except ValueError:
        # If the config entry was never loaded, we can just return True.
        unload_ok = True

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
