"""Initialize the Dual Thermostat integration."""

DOMAIN = "smart_climate"

async def async_setup(hass, config):
    """Set up the Dual Thermostat component."""
    # Global setup (if needed)
    return True


async def async_setup_entry(hass, entry):
    """Set up Dual Thermostat from a config entry."""
    # Store the config entry so we can reference it later.
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Instead of creating a background task, await the forward setup.
    result = await hass.config_entries.async_forward_entry_setup(entry, "climate")
    return result


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
