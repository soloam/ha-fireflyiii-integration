"""FireflyIII Integration Calendar Plataform"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional, cast

from homeassistant import config_entries, core
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant

from .const import (
    COORDINATOR,
    DOMAIN,
    FIREFLYIII_SENSOR_DESCRIPTIONS,
    EntityDescription,
    FireflyiiiEntityBase,
)
from .integrations.fireflyiii_functions import get_hass_locale, output_money
from .integrations.fireflyiii_objects import FireflyiiiBill, FireflyiiiObjectType

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

    user_locale = get_hass_locale(hass)

    bills = []
    for bill_id in coordinator.api_data.bills:
        obj = FireflyiiiBillCalendarEntity(
            coordinator,
            FIREFLYIII_SENSOR_DESCRIPTIONS[FireflyiiiObjectType.BILLS],
            bill_id,
            locale=user_locale,
        )

        bills.append(obj)

    sensors = []
    sensors.extend(bills)
    async_add_entities(sensors, update_before_add=True)


class FireflyiiiBillCalendarEntity(FireflyiiiEntityBase, CalendarEntity):
    """Firefly Bills Calendar"""

    _type = FireflyiiiObjectType.BILLS

    def __init__(
        self,
        coordinator,
        entity_description: Optional[EntityDescription] = None,
        fireflyiii_id: Optional[int] = None,
        locale: Optional[str] = None,
    ):
        super().__init__(coordinator, entity_description, fireflyiii_id, locale)

        self._attr_translation_placeholders = {"bill_name": self.entity_data.name}

        self._attr_supported_features: List[str] = []

    @property
    def entity_data(self) -> FireflyiiiBill:
        """Returns entity data - overide to Type Hints"""
        return cast(FireflyiiiBill, super().entity_data)

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

        events = self.fireflyiii_events(get_pay=True, get_paied=False)
        if events:
            return events[0]

        return None

    def fireflyiii_events(
        self, get_pay: Optional[bool] = True, get_paied: Optional[bool] = True
    ) -> List[CalendarEvent]:
        """Returns FireflyIII Events"""
        events = []

        if get_pay:
            for pay in self.entity_data.pay:
                start = pay.date.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(hours=24)

                event = CalendarEvent(
                    summary=f"{self.entity_data.name} {output_money(self.entity_data.value,self.entity_data.currency,self.locale)}",
                    start=start.date(),
                    end=end.date(),
                )
                events.append(event)

        if get_paied:
            for paid in self.entity_data.paid:
                start = paid.date.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(hours=24)

                event = CalendarEvent(
                    summary=f"✓ {self.entity_data.name} {output_money(paid.value,paid.currency,self.locale)}",
                    start=start.date(),
                    end=end.date(),
                )
                events.append(event)

        events.sort(key=lambda x: x.start, reverse=False)
        return events

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""

        return self.fireflyiii_events()
