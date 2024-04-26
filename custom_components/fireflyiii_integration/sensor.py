"""FireflyIII Integration Sensor Platform."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional, cast

from homeassistant import config_entries, core
from homeassistant.components.sensor import SensorEntity

from .const import (
    COORDINATOR,
    DOMAIN,
    FIREFLYIII_ACCOUNT_SENSOR_CONFIGS,
    FIREFLYIII_SENSOR_DESCRIPTIONS,
    STATE_UNAVAILABLE,
    FireflyiiiEntityBase,
    SensorEntityDescription,
)
from .integrations.fireflyiii_objects import (
    FireflyiiiAccount,
    FireflyiiiCategory,
    FireflyiiiObjectType,
)

_LOGGER = logging.getLogger(__name__)

# Time between updating data from Firefly
SCAN_INTERVAL = timedelta(minutes=10)


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

    accounts = []
    for account_id in coordinator.api_data.accounts:
        obj = FireflyiiiAccountSensorEntity(
            coordinator,
            FIREFLYIII_SENSOR_DESCRIPTIONS[FireflyiiiObjectType.ACCOUNTS],
            account_id,
        )
        accounts.append(obj)

    categories = []
    for category_id in coordinator.api_data.categories:
        obj = FireflyiiiCategorySensorEntity(
            coordinator,
            FIREFLYIII_SENSOR_DESCRIPTIONS[FireflyiiiObjectType.CATEGORIES],
            category_id,
        )

        categories.append(obj)

    budgets = []
    if FireflyiiiObjectType.BUDGETS in coordinator.api_data:
        obj = FireflyiiiBudgetSensorEntity(
            coordinator, FIREFLYIII_SENSOR_DESCRIPTIONS[FireflyiiiObjectType.BUDGETS]
        )

        budgets.append(obj)

    piggybank = []
    if FireflyiiiObjectType.PIGGY_BANKS in coordinator.api_data:
        obj = FireflyiiiPiggyBankSensorEntity(
            coordinator,
            FIREFLYIII_SENSOR_DESCRIPTIONS[FireflyiiiObjectType.PIGGY_BANKS],
        )

        piggybank.append(obj)

    sensors = []
    sensors.extend(accounts)
    sensors.extend(categories)
    sensors.extend(budgets)
    sensors.extend(piggybank)

    async_add_entities(sensors, update_before_add=True)


class FireflyiiiAccountSensorEntity(FireflyiiiEntityBase, SensorEntity):
    """Firefly Account Sensor"""

    _type = FireflyiiiObjectType.ACCOUNTS

    _attr_sources = ["account_type"]

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        fireflyiii_id: Optional[int] = None,
    ):
        super().__init__(coordinator, entity_description, fireflyiii_id)

        if (
            self.entity_data.type
            and self.entity_data.type in FIREFLYIII_ACCOUNT_SENSOR_CONFIGS
            and "icon" in FIREFLYIII_ACCOUNT_SENSOR_CONFIGS[self.entity_data.type]
        ):
            self._attr_icon = FIREFLYIII_ACCOUNT_SENSOR_CONFIGS[self.entity_data.type][
                "icon"
            ]

            self._attr_translation_key = FIREFLYIII_ACCOUNT_SENSOR_CONFIGS[
                self.entity_data.type
            ]["translation_key"]

            self._attr_translation_placeholders = {
                "account_name": self.entity_data.name
            }

    @property
    def entity_data(self) -> FireflyiiiAccount:
        """Returns entity data - overide to Type Hints"""
        return cast(FireflyiiiAccount, super().entity_data)

    @property
    def native_unit_of_measurement(self) -> str:

        currency_code = self.entity_data.currency

        if not currency_code:
            currency_code = self.coordinator.api_data.defaults.currency

        return currency_code

    @property
    def account_type(self) -> str:
        """Return FireflyIII account type"""
        return self.entity_data.type

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return self.entity_data.balance


class FireflyiiiCategorySensorEntity(FireflyiiiEntityBase, SensorEntity):
    """Firefly Category Sensor"""

    _type = FireflyiiiObjectType.CATEGORIES

    _total = 0

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        fireflyiii_id: Optional[int] = None,
    ):
        super().__init__(coordinator, entity_description, fireflyiii_id)

        self._attr_translation_placeholders = {"category_name": self.entity_data.name}

    @property
    def entity_data(self) -> FireflyiiiCategory:
        """Returns entity data - overide to Type Hints"""
        return cast(FireflyiiiCategory, super().entity_data)

    @property
    def native_unit_of_measurement(self) -> str:
        currency_code = self.entity_data.currency
        return currency_code if currency_code else ""

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""

        try:
            spent_val = float(self.entity_data.spent)
            earned_val = float(self.entity_data.earned)
            current_balance = spent_val + earned_val
        except ValueError:
            current_balance = STATE_UNAVAILABLE

        return current_balance


class FireflyiiiBudgetSensorEntity(FireflyiiiEntityBase, SensorEntity):
    """Firefly Budget Sensor"""

    _type = FireflyiiiObjectType.BUDGETS

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        data: Optional[dict] = None,
    ):
        self._data = data if data else {}
        super().__init__(coordinator, entity_description, self._data.get("id", 0))

        self._state = None


class FireflyiiiPiggyBankSensorEntity(FireflyiiiEntityBase, SensorEntity):
    """Firefly PiggyBank Sensor"""

    _type = FireflyiiiObjectType.PIGGY_BANKS

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        data: Optional[dict] = None,
    ):
        self._data = data if data else {}
        super().__init__(coordinator, entity_description, self._data.get("id", 0))

        self._state = None
