"""FireflyIII Integration Component."""

import logging

from homeassistant import config_entries, core
from homeassistant.const import CONF_NAME, CONF_URL, Platform
from homeassistant.helpers import device_registry

from .const import COORDINATOR, DATA, DOMAIN, MANUFACTURER
from .integrations.fireflyiii_coordinator import FireflyiiiCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.CALENDAR]


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)

    interval = 60

    # Update coordinator
    coordinator = FireflyiiiCoordinator(hass, interval, entry)

    hass.data[DOMAIN][entry.entry_id] = {DATA: hass_data, COORDINATOR: coordinator}

    # Fetch Initial Data
    await coordinator.async_refresh()

    device = device_registry.async_get(hass)
    device.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(DOMAIN, entry.entry_id)},
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get(CONF_NAME),
        manufacturer=MANUFACTURER,
        model=coordinator.api_data.get("about", {}).get("os", ""),
        sw_version=coordinator.api_data.get("about", {}).get("version", ""),
        configuration_url=entry.data.get(CONF_URL, ""),
    )

    # Forward the setup to the sensor platform.
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )
    return True


async def options_update_listener(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove config entry from domain.

        # pylint: disable=unused-variable
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


# pylint: disable=unused-argument
async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Disallow configuration via YAML."""
    return True
