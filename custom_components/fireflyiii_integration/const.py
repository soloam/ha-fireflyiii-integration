"""FireflyIII Constant File"""

# pylint: disable=unused-import

from typing import Any, Final, List, Mapping, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
    EntityDescription,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .integrations.fireflyiii_config import FireflyiiiConfig
from .integrations.fireflyiii_coordinator import FireflyiiiCoordinator
from .integrations.fireflyiii_objects import FireflyiiiObjectBase, FireflyiiiObjectType

DOMAIN = "fireflyiii_integration"
MANUFACTURER = "FireflyIII"

COORDINATOR = "coordinator"
DATA = "data"

STORE_VERSION = "1.0.0"
STORE_PREFIX = "fireflyiii"


# Account Type Mappings
FIREFLYIII_ACCOUNT_SENSOR_CONFIGS = {
    "asset": {"icon": "mdi:account-cash", "translation_key": "account_asset"},
    "expense": {"icon": "mdi:cash-minus", "translation_key": "account_expense"},
    "revenue": {"icon": "mdi:cash-plus", "translation_key": "account_revenue"},
    "liabilities": {"icon": "mdi:hand-coin", "translation_key": "account_liabiliti"},
    "cash": {"icon": "mdi:wallet-bifold", "translation_key": "account_cash"},
}

# Sensors Descriptions Classes
FIREFLYIII_SENSOR_DESCRIPTIONS: Final[dict[str, SensorEntityDescription]] = {
    FireflyiiiObjectType.SERVER: BinarySensorEntityDescription(
        key=FireflyiiiObjectType.SERVER,
        name="Server Status",
        icon="mdi:server",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FireflyiiiObjectType.ACCOUNTS: SensorEntityDescription(
        key=FireflyiiiObjectType.ACCOUNTS,
        icon="mdi:account-cash",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
    ),
    FireflyiiiObjectType.CATEGORIES: SensorEntityDescription(
        key=FireflyiiiObjectType.CATEGORIES,
        translation_key=FireflyiiiObjectType.CATEGORIES,
        icon="mdi:shape-plus",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
    ),
    FireflyiiiObjectType.BUDGETS: SensorEntityDescription(
        key=FireflyiiiObjectType.BUDGETS,
        name="Budget",
        icon="mdi:calculator",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
    ),
    FireflyiiiObjectType.PIGGY_BANKS: SensorEntityDescription(
        key=FireflyiiiObjectType.PIGGY_BANKS,
        translation_key=FireflyiiiObjectType.PIGGY_BANKS,
        icon="mdi:piggy-bank-outline",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
    ),
    FireflyiiiObjectType.BILLS: EntityDescription(
        key=FireflyiiiObjectType.BILLS,
        translation_key=FireflyiiiObjectType.BILLS,
        name="Bills",
        icon="mdi:invoice-clock-outline",
    ),
}


# Entity Base
class FireflyiiiEntityBase(CoordinatorEntity):
    """FireflyIII Entity base class"""

    _attr_sources: List[str] = []
    _type: FireflyiiiObjectType = FireflyiiiObjectType.NONE
    _attr_has_entity_name = True
    _user_config: Optional[FireflyiiiConfig] = None

    def __init__(
        self,
        coordinator: FireflyiiiCoordinator,
        entity_description: EntityDescription = None,
        fireflyiii_id=0,
        locale: Optional[str] = None,
    ):
        super().__init__(coordinator)

        self._fireflyiii_id = fireflyiii_id
        self._user_locale = locale

        if entity_description:
            self.entity_description = entity_description

        self._attr_unique_id = self.gerenate_unique_id()

    def gerenate_unique_id(self) -> str:
        """Returns Unique Id for entity"""
        return (
            f"{self.coordinator.config_entry.entry_id}_{self.key}_{self.fireflyiii_id}"
        )

    @property
    def locale(self) -> str:
        """User Locale"""
        return self._user_locale if self._user_locale else ""

    @property
    def fireflyiii_id(self) -> str:
        """Return FireflyIII object ID"""
        return self._fireflyiii_id

    @property
    def fireflyiii_type(self) -> str:
        """Return FireflyIII object Type"""
        return self._type

    @property
    def key(self):
        """Return FireflyIII generated key to UID"""

        if hasattr(self, "_type") and self._type:
            return self._type
        elif (
            hasattr(self, "entity_description")
            and hasattr(self.entity_description, "key")
            and self.entity_description.key
        ):
            return self.entity_description.key
        else:
            return self.__class__.__name__.lower()

    @property
    def entry_id(self):
        """Return EntryID"""
        return self.coordinator.config_entry.entry_id

    @property
    def config(self):
        """Return entry config"""
        return self.coordinator.config_entry

    @property
    def entry_data(self):
        """Return entry data"""

        if not self._user_config:
            self._user_config = FireflyiiiConfig(self.config.data)

        return self._user_config

    @property
    def _entity_data(self):
        """Return entity data from coordinator"""
        if not self.coordinator:
            return {}
        return self.coordinator.api_data.get(self._type, {})

    @property
    def object_type(self) -> FireflyiiiObjectType:
        """Returns FireflyIII object type"""
        return self._type

    @property
    def entity_data(self) -> FireflyiiiObjectBase:
        """Returns entity data"""
        return self._entity_data.get(self.fireflyiii_id, FireflyiiiConfig())

    @property
    def device_info(self) -> dict:
        """Return a description for device registry."""
        info = {
            "manufacturer": MANUFACTURER,
            "name": self.entry_data.name,
            "connections": {(DOMAIN, self.entry_id)},
        }

        return info

    @property
    def extra_state_attributes(self) -> Optional[Mapping[str, Any]]:
        """Return entity specific state attributes."""

        attributes = ["fireflyiii_type", "fireflyiii_id"]

        attributes.extend(self._attr_sources)

        state_attr = {}

        for attr in attributes:
            try:
                if getattr(self, attr) is not None:
                    state_attr[attr] = getattr(self, attr)
            except AttributeError:
                continue

        return state_attr
