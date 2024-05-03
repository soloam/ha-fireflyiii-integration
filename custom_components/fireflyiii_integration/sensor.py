"""FireflyIII Integration Sensor Platform."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
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
    FireflyiiiBudget,
    FireflyiiiCategory,
    FireflyiiiObjectType,
    FireflyiiiPiggyBank,
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

    piggybank = []
    for piggybank_id in coordinator.api_data.piggy_banks:
        obj = FireflyiiiPiggyBankSensorEntity(
            coordinator,
            FIREFLYIII_SENSOR_DESCRIPTIONS[FireflyiiiObjectType.PIGGY_BANKS],
            piggybank_id,
        )

        piggybank.append(obj)

    budgets = []
    for budget_id in coordinator.api_data.budgets:
        obj = FireflyiiiBudgetSensorEntity(
            coordinator,
            FIREFLYIII_SENSOR_DESCRIPTIONS[FireflyiiiObjectType.BUDGETS],
            budget_id,
        )

        budgets.append(obj)

    sensors = []
    sensors.extend(accounts)
    sensors.extend(categories)
    sensors.extend(budgets)
    sensors.extend(piggybank)

    async_add_entities(sensors, update_before_add=True)


class FireflyiiiAccountSensorEntity(FireflyiiiEntityBase, SensorEntity):
    """Firefly Account Sensor"""

    _type = FireflyiiiObjectType.ACCOUNTS

    _attr_sources = ["account_type", "balance_beginning", "balance_difference"]

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        fireflyiii_id: Optional[str] = None,
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

        return str(currency_code)

    @property
    def account_type(self) -> str:
        """Return FireflyIII account type"""
        return self.entity_data.type

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return self.entity_data.balance

    @property
    def balance_beginning(self) -> float:
        """Balance at the beginning of the time range"""
        return self.entity_data.balance_beginning

    @property
    def balance_difference(self) -> float:
        """Balance difference"""
        return self.entity_data.balance - self.entity_data.balance_beginning


class FireflyiiiCategorySensorEntity(FireflyiiiEntityBase, SensorEntity):
    """Firefly Category Sensor"""

    _type = FireflyiiiObjectType.CATEGORIES

    _total = 0

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        fireflyiii_id: Optional[str] = None,
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
        return str(currency_code) if currency_code else ""

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


class FireflyiiiPiggyBankSensorEntity(FireflyiiiEntityBase, SensorEntity):
    """Firefly PiggyBank Sensor"""

    _type = FireflyiiiObjectType.PIGGY_BANKS

    _attr_sources = [
        "percentage",
        "target_amount",
        "left_to_save",
        "account_name",
        "account_id",
    ]

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        fireflyiii_id: Optional[str] = None,
    ):
        super().__init__(coordinator, entity_description, fireflyiii_id)

        self._attr_translation_placeholders = {"piggy_bank_name": self.entity_data.name}

    @property
    def entity_data(self) -> FireflyiiiPiggyBank:
        """Returns entity data - overide to Type Hints"""
        return cast(FireflyiiiPiggyBank, super().entity_data)

    @property
    def native_unit_of_measurement(self) -> str:
        currency_code = self.entity_data.currency
        return str(currency_code) if currency_code else ""

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""

        return self.entity_data.current_amount

    @property
    def percentage(self) -> float:
        """Return percentage saved"""
        return self.entity_data.percentage

    @property
    def target_amount(self) -> float:
        """Return Target amount"""
        return self.entity_data.target_amount

    @property
    def left_to_save(self) -> float:
        """Return amount left to save"""
        return self.entity_data.left_to_save

    @property
    def account_name(self) -> str:
        """Returns account name"""
        if not self.entity_data.account:
            return ""
        return self.entity_data.account.name

    @property
    def account_id(self) -> str:
        """Returns account name"""
        if not self.entity_data.account:
            return ""
        return self.entity_data.account.id


class FireflyiiiBudgetSensorEntity(FireflyiiiEntityBase, SensorEntity):
    """Firefly Budget Sensor"""

    _type = FireflyiiiObjectType.BUDGETS

    _attr_sources = ["limit", "limit_start", "limit_end"]

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        fireflyiii_id: Optional[str] = None,
    ):
        super().__init__(coordinator, entity_description, fireflyiii_id)

        self._attr_translation_placeholders = {"budget_name": self.entity_data.name}

    @property
    def entity_data(self) -> FireflyiiiBudget:
        """Returns entity data - overide to Type Hints"""
        return cast(FireflyiiiBudget, super().entity_data)

    @property
    def native_unit_of_measurement(self) -> str:
        currency_code = self.entity_data.currency
        return str(currency_code) if currency_code else ""

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""

        return self.entity_data.spent

    @property
    def limit(self) -> float:
        """Return the budget limit"""

        return self.entity_data.limit

    @property
    def limit_start(self) -> Optional[datetime]:
        """Return the budget limit start date"""

        return self.entity_data.limit_start

    @property
    def limit_end(self) -> Optional[datetime]:
        """Return the budget limit end date"""

        return self.entity_data.limit_end
