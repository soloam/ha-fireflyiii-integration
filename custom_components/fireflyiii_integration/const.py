"""FireflyIII Constant File"""

# pylint: disable=unused-import

from typing import Any, Final, Mapping, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
    EntityDescription,
)
from homeassistant.components.calendar import CalendarEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_NAME,
    CONF_PATH,
    CONF_URL,
    WEEKDAYS,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "fireflyiii_integration"
MANUFACTURER = "FireflyIII"

ATTR_CLONES = "clones"
ATTR_CLONES_UNIQUE = "clones_unique"
ATTR_FORKS = "forks"
ATTR_LATEST_COMMIT_MESSAGE = "latest_commit_message"
ATTR_LATEST_COMMIT_SHA = "latest_commit_sha"
ATTR_LATEST_OPEN_ISSUE_URL = "latest_open_issue_url"
ATTR_LATEST_OPEN_PULL_REQUEST_URL = "latest_open_pull_request_url"
ATTR_LATEST_RELEASE_TAG = "latest_release_tag"
ATTR_LATEST_RELEASE_URL = "latest_release_url"
ATTR_OPEN_ISSUES = "open_issues"
ATTR_OPEN_PULL_REQUESTS = "open_pull_requests"
ATTR_PATH = "path"
ATTR_STARGAZERS = "stargazers"
ATTR_VIEWS = "views"
ATTR_VIEWS_UNIQUE = "views_unique"


COORDINATOR = "coordinator"
DATA = "data"

STORE_VERSION = "1.0.0"
STORE_PREFIX = "fireflyiii"


CONF_NAME_DEFAULT = "FireflyIII"


CONF_DATE_LASTX_DAYS_TYPE = "d"
CONF_DATE_LASTX_WEEKS_TYPE = "w"
CONF_DATE_LASTX_YEARS_TYPE = "y"

CONF_DATE_LASTX_BACK_TYPES = [
    CONF_DATE_LASTX_DAYS_TYPE,
    CONF_DATE_LASTX_WEEKS_TYPE,
    CONF_DATE_LASTX_YEARS_TYPE,
]

CONF_RETURN_RANGE_YEAR_TYPE = "year"
CONF_RETURN_RANGE_MONTH_TYPE = "month"
CONF_RETURN_RANGE_WEEK_TYPE = "week"
CONF_RETURN_RANGE_DAY_TYPE = "day"
CONF_RETURN_RANGE_LASTX_TYPE = "lastx"

CONF_RETURN_RANGE_TYPES = [
    CONF_RETURN_RANGE_YEAR_TYPE,
    CONF_RETURN_RANGE_MONTH_TYPE,
    CONF_RETURN_RANGE_WEEK_TYPE,
    CONF_RETURN_RANGE_DAY_TYPE,
    CONF_RETURN_RANGE_LASTX_TYPE,
]

CONF_RETURN_ACCOUNT_TYPES = ["asset", "expense", "revenue", "liabilities", "cash"]
CONF_RETURN_ACCOUNT_TYPE_DEFAULT = ["asset"]

CONF_RETURN_ACCOUNTS = "return_accounts"
CONF_RETURN_ACCOUNTS_DEFAULT = True
CONF_RETURN_ACCOUNT_ID = "return_accounts_ids"
CONF_RETURN_BUDGETS = "return_budgets"
CONF_RETURN_BUDGETS_DEFAULT = False
CONF_RETURN_PIGGY_BANKS = "return_piggy_banks"
CONF_RETURN_PIGGY_BANKS_DEFAULT = False
CONF_RETURN_CATEGORIES = "return_categories"
CONF_RETURN_CATEGORIES_DEFAULT = True
CONF_RETURN_CATEGORIES_ID = "return_category_ids"
CONF_RETURN_INVOICES = "return_invoices"
CONF_RETURN_INVOICES_DEFAULT = True
CONF_RETURN_RANGE = "return_range"
CONF_RETURN_RANGE_DEFAULT = CONF_RETURN_RANGE_MONTH_TYPE

CONF_RETURN_ACCOUNT_TYPE = "return_account_type"

CONF_DATE_MONTH_START = "date_month_start"
CONF_DATE_WEEK_START = "date_week_start"
CONF_DATE_YEAR_START = "date_year_start"

CONF_DATE_LASTX_BACK_TYPE = "date_lastx_back_type"
CONF_DATE_LASTX_BACK = "date_lastx_back"

FIREFLYIII_SERVER_SENSOR_TYPE = "server"
FIREFLYIII_ACCOUNT_SENSOR_TYPE = "account"
FIREFLYIII_CATEGORY_SENSOR_TYPE = "category"
FIREFLYIII_BUDGET_SENSOR_TYPE = "budget"
FIREFLYIII_INVOICES_SENSOR_TYPE = "invoices"
FIREFLYIII_PIGGYBANK_SENSOR_TYPE = "piggy_bank"

FIREFLYIII_ACCOUNT_SENSOR_CONFIGS = {
    "asset": {"icon": "mdi:account-cash", "translation_key": "account_asset"},
    "expense": {"icon": "mdi:cash-minus", "translation_key": "account_expense"},
    "revenue": {"icon": "mdi:cash-plus", "translation_key": "account_revenue"},
    "liabilities": {"icon": "mdi:hand-coin", "translation_key": "account_liabiliti"},
    "cash": {"icon": "mdi:wallet-bifold", "translation_key": "account_cash"},
}

# Servers Descriptions
FIREFLYIII_SENSOR_TYPES: Final[dict[str, SensorEntityDescription]] = {
    FIREFLYIII_SERVER_SENSOR_TYPE: BinarySensorEntityDescription(
        key=FIREFLYIII_SERVER_SENSOR_TYPE,
        name="Server Status",
        icon="mdi:server",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FIREFLYIII_ACCOUNT_SENSOR_TYPE: SensorEntityDescription(
        key=FIREFLYIII_ACCOUNT_SENSOR_TYPE,
        icon="mdi:account-cash",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
    ),
    FIREFLYIII_CATEGORY_SENSOR_TYPE: SensorEntityDescription(
        key=FIREFLYIII_CATEGORY_SENSOR_TYPE,
        translation_key=FIREFLYIII_CATEGORY_SENSOR_TYPE,
        icon="mdi:shape-plus",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
    ),
    FIREFLYIII_BUDGET_SENSOR_TYPE: SensorEntityDescription(
        key=FIREFLYIII_BUDGET_SENSOR_TYPE,
        name="Budget",
        icon="mdi:calculator",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
    ),
    FIREFLYIII_PIGGYBANK_SENSOR_TYPE: SensorEntityDescription(
        key=FIREFLYIII_PIGGYBANK_SENSOR_TYPE,
        name="Piggy Bank",
        icon="mdi:piggy-bank-outline",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
    ),
    FIREFLYIII_INVOICES_SENSOR_TYPE: EntityDescription(
        key=FIREFLYIII_INVOICES_SENSOR_TYPE,
        name="Invoices",
        icon="mdi:invoice-clock-outline",
    ),
}


# Entity Base
class FireflyiiiEntityBase(CoordinatorEntity):
    """FireflyIII Entity base class"""

    _attr_sources = []

    _type = ""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator, entity_description: EntityDescription = None, fireflyiii_id=0
    ):
        super().__init__(coordinator)

        self._fireflyiii_id = fireflyiii_id

        if entity_description:
            self.entity_description = entity_description

        self._attr_unique_id = self.gerenate_unique_id()

    def gerenate_unique_id(self) -> str:
        """Returns Unique Id for entity"""
        return (
            f"{self.coordinator.config_entry.entry_id}_{self.key}_{self.fireflyiii_id}"
        )

    @property
    def fireflyiii_id(self):
        """Return FireflyIII object ID"""
        return self._fireflyiii_id

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
        return self.config.data

    @property
    def _entity_data(self):
        """Return entity data from coordinator"""
        if not self.coordinator:
            return {}

        return self.coordinator.api_data.get(self._type, {}).get(self.fireflyiii_id, {})

    @property
    def fireflyiii_type(self) -> str:
        """Returns FireflyIII object type"""
        return self._type

    @property
    def entity_start_data(self):
        """Returns entity data from the start of the range"""

        entity_data = self._entity_data

        # Returns The Desired State to the entity
        if "start_state" in entity_data:
            return entity_data["start_state"]
        elif "end_state" in entity_data:
            return entity_data["end_state"]
        elif "attributes" in entity_data:
            return entity_data
        else:
            return {}

    @property
    def entity_end_data(self):
        """Returns entity data from the end of the range"""

        entity_data = self._entity_data

        # Returns The Desired State to the entity
        if "end_state" in entity_data:
            return entity_data["end_state"]
        elif "start_state" in entity_data:
            return entity_data["start_state"]
        elif "attributes" in entity_data:
            return entity_data
        else:
            return {}

    @property
    def entity_data(self):
        """Returns entity data"""

        entity_data = self._entity_data

        # Returns The Desired State to the entity
        if "end_state" in entity_data:
            return entity_data["end_state"]
        elif "start_state" in entity_data:
            return entity_data["start_state"]
        elif "attributes" in entity_data:
            return entity_data
        else:
            return {}

    @property
    def device_info(self) -> dict:
        """Return a description for device registry."""
        info = {
            "manufacturer": MANUFACTURER,
            "name": self.entry_data[CONF_NAME],
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
