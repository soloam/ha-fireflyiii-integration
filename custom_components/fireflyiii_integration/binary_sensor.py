"""FireflyIII Integration Sensor platform"""

from __future__ import annotations

import logging

from homeassistant import config_entries, core
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import (
    COORDINATOR,
    DOMAIN,
    FIREFLYIII_SENSOR_TYPES,
    FIREFLYIII_SERVER_SENSOR_TYPE,
    BinarySensorEntityDescription,
    FireflyiiiEntityBase,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    # Update our config to include new repos and remove those that have been removed.
    if config_entry.options:
        config.update(config_entry.options)

    coordinator = config[COORDINATOR]

    sensors = [
        FireflyiiiServer(
            coordinator, FIREFLYIII_SENSOR_TYPES[FIREFLYIII_SERVER_SENSOR_TYPE]
        )
    ]
    async_add_entities(sensors, update_before_add=True)


class FireflyiiiServer(FireflyiiiEntityBase, BinarySensorEntity):
    """Firefly Server Sensors"""

    def __init__(
        self, coordinator, entity_description: BinarySensorEntityDescription = None
    ):
        super().__init__(coordinator, entity_description)

        self._available = True

    @property
    def is_on(self) -> bool:
        """Return if connected."""
        return self.coordinator.last_update_success
