"""FireflyIII Integration Sensor platform"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Mapping, Optional

from homeassistant import config_entries, core
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import (
    COORDINATOR,
    DOMAIN,
    FIREFLYIII_SENSOR_DESCRIPTIONS,
    BinarySensorEntityDescription,
    FireflyiiiEntityBase,
)
from .integrations.fireflyiii_objects import FireflyiiiObjectType

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
        FireflyiiiServerBinarySensorEntity(
            coordinator, FIREFLYIII_SENSOR_DESCRIPTIONS[FireflyiiiObjectType.SERVER]
        )
    ]
    async_add_entities(sensors, update_before_add=True)


class FireflyiiiServerBinarySensorEntity(FireflyiiiEntityBase, BinarySensorEntity):
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

    @property
    def start_date(self) -> Optional[datetime]:
        """Import Start Date Time"""
        timerange = self.coordinator.timerange
        if not timerange:
            return None

        return timerange.start_datetime

    @property
    def end_date(self) -> Optional[datetime]:
        """Import End Date Time"""
        timerange = self.coordinator.timerange
        if not timerange:
            return None

        return timerange.end_datetime

    @property
    def extra_state_attributes(self) -> Optional[Mapping[str, Any]]:
        """Return entity specific state attributes."""

        attributes = ["start_date", "end_date"]

        state_attr = {}

        for attr in attributes:
            try:
                if getattr(self, attr) is not None:
                    state_attr[attr] = getattr(self, attr)
            except AttributeError:
                continue

        return state_attr
