"""FireflyIII Integration Sensor Platform."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant import config_entries, core
from homeassistant.components.sensor import SensorEntity

from .const import (
    COORDINATOR,
    DOMAIN,
    FIREFLYIII_ACCOUNT_SENSOR_CONFIGS,
    FIREFLYIII_ACCOUNT_SENSOR_TYPE,
    FIREFLYIII_BUDGET_SENSOR_TYPE,
    FIREFLYIII_CATEGORY_SENSOR_TYPE,
    FIREFLYIII_PIGGYBANK_SENSOR_TYPE,
    FIREFLYIII_SENSOR_TYPES,
    FireflyiiiEntityBase,
    SensorEntityDescription,
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
    if FIREFLYIII_ACCOUNT_SENSOR_TYPE in coordinator.api_data:
        for account_id, _ in coordinator.api_data[
            FIREFLYIII_ACCOUNT_SENSOR_TYPE
        ].items():

            obj = FireflyiiiAccount(
                coordinator,
                FIREFLYIII_SENSOR_TYPES[FIREFLYIII_ACCOUNT_SENSOR_TYPE],
                account_id,
            )

            accounts.append(obj)

    categories = []
    if FIREFLYIII_CATEGORY_SENSOR_TYPE in coordinator.api_data:
        for category_id in coordinator.api_data[FIREFLYIII_CATEGORY_SENSOR_TYPE]:
            obj = FireflyiiiCategory(
                coordinator,
                FIREFLYIII_SENSOR_TYPES[FIREFLYIII_CATEGORY_SENSOR_TYPE],
                category_id,
            )

            categories.append(obj)

    budgets = []
    if FIREFLYIII_BUDGET_SENSOR_TYPE in coordinator.api_data:
        obj = FireflyiiiBudget(
            coordinator, FIREFLYIII_SENSOR_TYPES[FIREFLYIII_BUDGET_SENSOR_TYPE]
        )

        budgets.append(obj)

    piggybank = []
    if FIREFLYIII_PIGGYBANK_SENSOR_TYPE in coordinator.api_data:
        obj = FireflyiiiPiggyBank(
            coordinator, FIREFLYIII_SENSOR_TYPES[FIREFLYIII_PIGGYBANK_SENSOR_TYPE]
        )

        piggybank.append(obj)

    sensors = []
    sensors.extend(accounts)
    sensors.extend(categories)
    sensors.extend(budgets)
    sensors.extend(piggybank)

    async_add_entities(sensors, update_before_add=True)


class FireflyiiiAccount(FireflyiiiEntityBase, SensorEntity):
    """Firefly Account Sensor"""

    _type = FIREFLYIII_ACCOUNT_SENSOR_TYPE

    _attr_sources = ["account_type"]

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        fireflyiii_id: int = None,
    ):
        super().__init__(coordinator, entity_description, fireflyiii_id)

        account_attributes = self.entity_data.get("attributes", {})

        self._account_type = account_attributes.get("type", None)

        if (
            self._account_type
            and self._account_type in FIREFLYIII_ACCOUNT_SENSOR_CONFIGS
            and "icon" in FIREFLYIII_ACCOUNT_SENSOR_CONFIGS[self._account_type]
        ):
            self._attr_icon = FIREFLYIII_ACCOUNT_SENSOR_CONFIGS[self._account_type][
                "icon"
            ]

            self._attr_translation_key = FIREFLYIII_ACCOUNT_SENSOR_CONFIGS[
                self._account_type
            ]["translation_key"]

            self._attr_translation_placeholders = {
                "account_name": account_attributes.get("name", "")
            }

    @property
    def native_unit_of_measurement(self) -> str:
        account_attributes = self.entity_data.get("attributes", {})

        currency_code = account_attributes.get("currency_code", "")

        if not currency_code:
            currency_code = self.coordinator.api_data.get("default_currency", "")

        return currency_code

    @property
    def account_type(self) -> str:
        """Return FireflyIII account type"""
        return self._account_type

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""

        account_attributes = self.entity_data.get("attributes", {})
        return account_attributes.get("current_balance", None)


class FireflyiiiCategory(FireflyiiiEntityBase, SensorEntity):
    """Firefly Category Sensor"""

    _type = FIREFLYIII_CATEGORY_SENSOR_TYPE

    _total = 0

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        fireflyiii_id: int = None,
    ):
        super().__init__(coordinator, entity_description, fireflyiii_id)

        account_attributes = self.entity_data.get("attributes", {})

        self._attr_translation_placeholders = {
            "category_name": account_attributes.get("name", "")
        }

    @property
    def native_unit_of_measurement(self) -> str:
        account_attributes = self.entity_data.get("attributes", {})
        spent = account_attributes.get("spent", [{}])
        earned = account_attributes.get("earned", [{}])

        spent = [{}] if len(spent) == 0 else spent
        earned = [{}] if len(earned) == 0 else earned

        currency_code = spent[0].get("currency_code", "")
        if not currency_code:
            currency_code = earned[0].get("currency_code", "")

        if not currency_code:
            currency_code = self.coordinator.api_data.get("default_currency", "")

        return currency_code

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        account_attributes = self.entity_data.get("attributes", {})
        spent = account_attributes.get("spent", [{}])
        earned = account_attributes.get("earned", [{}])

        spent = [{}] if len(spent) == 0 else spent
        earned = [{}] if len(earned) == 0 else earned

        try:
            spent_val = float(spent[0].get("sum", 0))
            earned_val = float(earned[0].get("sum", 0))
            current_balance = spent_val + earned_val
        except ValueError:
            current_balance = None

        return current_balance


class FireflyiiiBudget(FireflyiiiEntityBase, SensorEntity):
    """Firefly Budget Sensor"""

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        data: dict = None,
    ):
        self._data = data if data else {}
        super().__init__(coordinator, entity_description, self._data.get("id", 0))

        self._state = None


class FireflyiiiPiggyBank(FireflyiiiEntityBase, SensorEntity):
    """Firefly PiggyBank Sensor"""

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription = None,
        data: dict = None,
    ):
        self._data = data if data else {}
        super().__init__(coordinator, entity_description, self._data.get("id", 0))

        self._state = None
