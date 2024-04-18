"""FireflyIII Integration Calendar Plataform"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from homeassistant import config_entries, core
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant

from .const import (
    COORDINATOR,
    DOMAIN,
    FIREFLYIII_INVOICES_SENSOR_TYPE,
    FIREFLYIII_SENSOR_TYPES,
    EntityDescription,
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

    invoices = []
    if FIREFLYIII_INVOICES_SENSOR_TYPE in coordinator.api_data:
        obj = FireflyiiiInvoices(
            coordinator, FIREFLYIII_SENSOR_TYPES[FIREFLYIII_INVOICES_SENSOR_TYPE]
        )

        invoices.append(obj)

    sensors = []
    sensors.extend(invoices)
    async_add_entities(sensors, update_before_add=True)


class FireflyiiiInvoices(FireflyiiiEntityBase, CalendarEntity):
    """Firefly Invoices Calendar"""

    def __init__(
        self,
        coordinator,
        entity_description: EntityDescription = None,
        data: dict = None,
    ):
        self._data = data if data else {}
        super().__init__(coordinator, entity_description, self._data.get("id", 0))

        self._attr_supported_features = []

        self._available = True

    async def async_create_event(self, **kwargs: Any) -> None:
        pass

    async def async_delete_event(
        self,
        uid: str,
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        pass

    async def async_update_event(
        self,
        uid: str,
        event: dict[str, Any],
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        pass

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return []
