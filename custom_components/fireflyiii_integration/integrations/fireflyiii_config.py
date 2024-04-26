"""
FireflyIII Integration Config Agregator

Defines a base to the config
"""

from collections import UserDict
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, List, Optional, cast

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_URL, WEEKDAYS
from homeassistant.helpers import selector

from .fireflyiii import Fireflyiii
from .fireflyiii_objects import FireflyiiiCurrency

try:
    from ..const_dev import CONF_ACCESS_TOKEN_DEFAULT, CONF_URL_DEFAULT
except ModuleNotFoundError as err:
    CONF_ACCESS_TOKEN_DEFAULT = ""
    CONF_URL_DEFAULT = ""

CONF_DATE_LASTX_BACK = "date_lastx_back"
CONF_DATE_LASTX_BACK_TYPE = "date_lastx_back_type"
CONF_DATE_LASTX_DAYS_TYPE = "d"
CONF_DATE_LASTX_WEEKS_TYPE = "w"
CONF_DATE_LASTX_YEARS_TYPE = "y"
CONF_DATE_MONTH_START = "date_month_start"
CONF_DATE_WEEK_START = "date_week_start"
CONF_DATE_YEAR_START = "date_year_start"
CONF_RETURN_ACCOUNT_ID = "return_accounts_ids"
CONF_RETURN_ACCOUNT_TYPE = "return_account_type"
CONF_RETURN_ACCOUNT_TYPES = ["asset", "expense", "revenue", "liabilities", "cash"]
CONF_RETURN_ACCOUNTS = "return_accounts"
CONF_RETURN_BILLS = "return_bills"
CONF_RETURN_BUDGETS = "return_budgets"
CONF_RETURN_CATEGORIES = "return_categories"
CONF_RETURN_CATEGORIES_ID = "return_category_ids"
CONF_RETURN_CURRENCY = "return_currency"
CONF_RETURN_PIGGY_BANKS = "return_piggy_banks"
CONF_RETURN_RANGE = "return_range"
CONF_RETURN_RANGE_DAY_TYPE = "day"
CONF_RETURN_RANGE_LASTX_TYPE = "lastx"
CONF_RETURN_RANGE_MONTH_TYPE = "month"
CONF_RETURN_RANGE_WEEK_TYPE = "week"
CONF_RETURN_RANGE_YEAR_TYPE = "year"

CONF_NAME_DEFAULT = "FireflyIII"
CONF_RETURN_ACCOUNT_TYPE_DEFAULT = ["asset"]
CONF_RETURN_ACCOUNTS_DEFAULT = True
CONF_RETURN_BILLS_DEFAULT = True
CONF_RETURN_BUDGETS_DEFAULT = False
CONF_RETURN_CATEGORIES_DEFAULT = True
CONF_RETURN_PIGGY_BANKS_DEFAULT = False
CONF_RETURN_RANGE_DEFAULT = CONF_RETURN_RANGE_MONTH_TYPE

CONF_DATE_LASTX_BACK_TYPES = [
    CONF_DATE_LASTX_DAYS_TYPE,
    CONF_DATE_LASTX_WEEKS_TYPE,
    CONF_DATE_LASTX_YEARS_TYPE,
]

CONF_RETURN_RANGE_TYPES = [
    CONF_RETURN_RANGE_YEAR_TYPE,
    CONF_RETURN_RANGE_MONTH_TYPE,
    CONF_RETURN_RANGE_WEEK_TYPE,
    CONF_RETURN_RANGE_DAY_TYPE,
    CONF_RETURN_RANGE_LASTX_TYPE,
]


class FireflyiiiConfig(UserDict):
    """Fireflyiii Configuration"""

    # pylint: disable=[unused-argument,redefined-builtin]
    def __init__(self, dict=None, /, **kwargs) -> None:
        super().__init__(cast(UserDict, dict))

        self._api: Optional[Fireflyiii] = None
        self._api_data: Dict["str", Any] = {}

    async def get_api(self) -> Fireflyiii:
        """Returns the fireflyiii api"""

        if self._api:
            return self._api

        api = Fireflyiii(host=self.host, access_token=self.access_token)
        self._api = api

        if not self._api_data:
            await self.get_api_data()

        return self._api

    async def get_api_data(self):
        """Loads Api data into memory"""

        if self._api_data:
            return self._api_data

        api = await self.get_api()
        if not await api.check_connection():
            return

        self._api_data = {}
        self._api_data["start_year"] = await api.start_year
        self._api_data["accounts_autocomplete"] = await api.accounts_autocomplete
        self._api_data["categories_autocomplete"] = await api.categories_autocomplete
        self._api_data["enabled_currencies"] = await api.currencies(enabled=True)

        self._api_data["default_currency"] = await api.default_currency

    @property
    def name(self) -> str:
        """Firefly config name"""
        return self.get(CONF_NAME, CONF_NAME_DEFAULT)

    @property
    def host(self) -> str:
        """Firefly config host"""
        return self.get(CONF_URL, CONF_URL_DEFAULT)

    @property
    def access_token(self) -> str:
        """Firefly config access token"""
        return self.get(CONF_ACCESS_TOKEN, CONF_ACCESS_TOKEN_DEFAULT)

    @property
    def get_budgets(self) -> bool:
        """Firefly config should return budgets"""
        return self.get(CONF_RETURN_BUDGETS, CONF_RETURN_BUDGETS_DEFAULT)

    @property
    def get_bills(self) -> bool:
        """Firefly config should return bills"""
        return self.get(CONF_RETURN_BILLS, CONF_RETURN_BILLS_DEFAULT)

    @property
    def get_piggy_banks(self) -> bool:
        """Firefly config should return piggy banks"""
        return self.get(CONF_RETURN_PIGGY_BANKS, CONF_RETURN_PIGGY_BANKS_DEFAULT)

    @property
    def get_categories(self) -> bool:
        """Firefly config should return categries"""
        return self.get(CONF_RETURN_CATEGORIES, CONF_RETURN_CATEGORIES_DEFAULT)

    @property
    def get_accounts(self) -> bool:
        """Firefly config should return accounts"""
        return self.get(CONF_RETURN_ACCOUNTS, CONF_RETURN_ACCOUNTS_DEFAULT)

    @property
    def date_range_type(self) -> str:
        """Firefly config date range type"""
        return self.get(CONF_RETURN_RANGE, CONF_RETURN_RANGE_DEFAULT)

    @property
    def categories_ids(self) -> List[str]:
        """Firefly config list of category id's to return"""
        return self.get(CONF_RETURN_CATEGORIES_ID, [])

    @property
    def categories_autocomplete(self):
        """Firefly config category list - helper"""
        return self._api_data["categories_autocomplete"]

    @property
    def account_types(self) -> List[str]:
        """Firefly config account tyes - helper"""
        return self.get(CONF_RETURN_ACCOUNT_TYPE, CONF_RETURN_ACCOUNT_TYPE_DEFAULT)

    @property
    def get_account_types(self) -> List[str]:
        """Firefly config get this tye of accounts"""
        return CONF_RETURN_ACCOUNT_TYPES

    @property
    def account_ids(self) -> List[str]:
        """Firefly config list of account id's to return"""
        return self.get(CONF_RETURN_ACCOUNT_ID, [])

    @property
    def accounts_autocomplete(self):
        """Firefly config accounts list - helper"""
        return self._api_data["accounts_autocomplete"]

    @property
    def is_date_range_year(self) -> bool:
        """Firefly config is ranged in years - flag"""
        return self.date_range_type == CONF_RETURN_RANGE_YEAR_TYPE

    @property
    def is_date_range_month(self) -> bool:
        """Firefly config is ranged in months - flag"""
        return self.date_range_type == CONF_RETURN_RANGE_MONTH_TYPE

    @property
    def is_date_range_week(self) -> bool:
        """Firefly config is ranged in weeks - flag"""
        return self.date_range_type == CONF_RETURN_RANGE_WEEK_TYPE

    @property
    def is_date_range_day(self) -> bool:
        """Firefly config is ranged in days - flag"""
        return self.date_range_type == CONF_RETURN_RANGE_DAY_TYPE

    @property
    def is_date_range_lastx(self) -> bool:
        """Firefly config is ranged in custum - flag"""
        return self.date_range_type == CONF_RETURN_RANGE_LASTX_TYPE

    @property
    def year_start(self) -> str:
        """Firefly config year start"""
        base_default = f"{datetime.today().year}-01-01"

        default = self._api_data.get("start_year", base_default)
        return self.get(CONF_DATE_YEAR_START, default)

    @property
    def month_start(self) -> int:
        """Firefly config month start"""
        day = self.get(CONF_DATE_MONTH_START, 1)
        try:
            day = int(day)
        except ValueError:
            day = 1

        return day

    @property
    def week_start(self) -> str:
        """Firefly Config Start of the week"""
        return self.get(CONF_DATE_WEEK_START, WEEKDAYS[0])

    @property
    def lastx_days(self) -> dict:
        """Firefly Config Custum Back Time"""
        back = self.get(CONF_DATE_LASTX_BACK, 1)

        try:
            back = int(back)
        except ValueError:
            back = 1

        return {
            "back": back,
            "type": self.get(CONF_DATE_LASTX_BACK_TYPE, CONF_DATE_LASTX_BACK_TYPES[0]),
        }

    @property
    def is_lastx_days_type_years(self) -> bool:
        """Check if custom time is in years"""
        return self.lastx_days.get("type") == CONF_DATE_LASTX_YEARS_TYPE

    @property
    def is_lastx_days_type_weeks(self) -> bool:
        """Check if custom time is in weeks"""
        return self.lastx_days.get("type") == CONF_DATE_LASTX_WEEKS_TYPE

    @property
    def is_lastx_days_type_days(self) -> bool:
        """Check if custom time is in days"""
        return self.lastx_days.get("type") == CONF_DATE_LASTX_DAYS_TYPE

    @property
    def currency(self) -> FireflyiiiCurrency:
        """Return Currency"""
        return self._api_data.get("default_currency", self.default_currency)

    @property
    def default_currency(self) -> FireflyiiiCurrency:
        """Default Currency"""
        return self._api_data.get("default_currency", "")

    @property
    def enabled_currencies(self) -> List[FireflyiiiCurrency]:
        """Ebabled Currencies"""
        return self._api_data.get("enabled_currencies", {})


class FireflyiiiConfigSchema:
    """FireflyIII Config Flow Schemas"""

    _data_source: Optional[FireflyiiiConfig] = None

    def __init__(self):
        raise NotImplementedError()

    @classmethod
    def set_data_source(cls, source: FireflyiiiConfig):
        """Sets data source for the config"""

        if isinstance(source, FireflyiiiConfig):
            data_source = source
        elif isinstance(source, dict):
            data_source = FireflyiiiConfig(source)
        elif isinstance(source, MappingProxyType):
            data_source = FireflyiiiConfig(dict(source))
        else:
            return

        cls._data_source = data_source

    @classmethod
    def data_source(cls) -> FireflyiiiConfig:
        """Gets the data source"""

        if not isinstance(cls._data_source, FireflyiiiConfig):
            cls._data_source = FireflyiiiConfig()

        return cls._data_source

    @classmethod
    def name(cls):
        """Config flow name field"""
        return {vol.Required(CONF_NAME, default=cls.data_source().name): cv.string}

    @classmethod
    def access_token(cls):
        """Config flow access token field"""
        return {
            vol.Required(
                CONF_ACCESS_TOKEN, default=cls.data_source().access_token
            ): cv.string
        }

    @classmethod
    def url(cls):
        """Config flow url field"""
        return {vol.Required(CONF_URL, default=cls.data_source().host): cv.string}

    @classmethod
    def currency(cls):
        """Config flow currency field"""
        return {
            vol.Required(
                CONF_RETURN_CURRENCY, default=str(cls.data_source().currency)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    multiple=False,
                    custom_value=False,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    options=[
                        {
                            "label": f"{currency.name} ({currency.code})",
                            "value": currency.code,
                        }
                        for _, currency in cls.data_source().enabled_currencies.items()
                    ],
                )
            )
        }

    @classmethod
    def schema_auth(cls):
        """Config flow Schema auth"""
        schema = {}
        schema.update(cls.name())
        schema.update(cls.url())
        schema.update(cls.access_token())
        return vol.Schema(schema)

    @classmethod
    def _return_this(cls, name: str, default=None):
        """Config flow builded to get somthing"""
        kargs = {}
        if default:
            kargs = {"default": default}

        return {vol.Optional(name, **kargs): cv.boolean}

    @classmethod
    def return_budgets(cls):
        """Config flow return budgets"""
        return cls._return_this(CONF_RETURN_BUDGETS, cls.data_source().get_budgets)

    @classmethod
    def return_bills(cls):
        """Config flow return bills"""
        return cls._return_this(CONF_RETURN_BILLS, cls.data_source().get_bills)

    @classmethod
    def return_piggy_banks(cls):
        """Config flow return piggy banks"""
        return cls._return_this(
            CONF_RETURN_PIGGY_BANKS, cls.data_source().get_piggy_banks
        )

    @classmethod
    def return_categories(cls):
        """Config flow return categories"""
        return cls._return_this(
            CONF_RETURN_CATEGORIES, cls.data_source().get_categories
        )

    @classmethod
    def return_accounts(cls):
        """Config flow return accounts"""
        return cls._return_this(CONF_RETURN_ACCOUNTS, cls.data_source().get_accounts)

    @classmethod
    def return_range(cls):
        """Config flow return range type"""
        return {
            vol.Required(
                CONF_RETURN_RANGE, default=cls.data_source().date_range_type
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=CONF_RETURN_RANGE_TYPES,
                    translation_key=CONF_RETURN_RANGE,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }

    @classmethod
    def schema_sensor(cls):
        """Config flow Schema sensors"""
        schema = {}
        schema.update(cls.currency())
        schema.update(cls.return_budgets())
        schema.update(cls.return_bills())
        schema.update(cls.return_piggy_banks())
        schema.update(cls.return_categories())
        schema.update(cls.return_accounts())
        schema.update(cls.return_range())
        return vol.Schema(schema)

    @classmethod
    def categories_ids(cls):
        """Config flow return category id's"""
        return {
            vol.Optional(
                CONF_RETURN_CATEGORIES_ID, default=cls.data_source().categories_ids
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    multiple=True,
                    custom_value=False,
                    # pylint: disable=line-too-long
                    options=[
                        {"label": category.name, "value": category_id}
                        for category_id, category in cls.data_source().categories_autocomplete.categories.items()
                    ],
                )
            )
        }

    @classmethod
    def account_types(cls):
        """Config flow return account types"""
        return {
            vol.Required(
                CONF_RETURN_ACCOUNT_TYPE,
                default=cls.data_source().account_types,
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=CONF_RETURN_ACCOUNT_TYPES,
                    translation_key=CONF_RETURN_ACCOUNT_TYPE,
                    multiple=True,
                )
            )
        }

    @classmethod
    def account_ids(cls):
        """Config flow return account id's"""
        return {
            vol.Optional(
                CONF_RETURN_ACCOUNT_ID, default=cls.data_source().account_ids
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    multiple=True,
                    custom_value=False,
                    # pylint: disable=line-too-long
                    options=[
                        {"label": account.name, "value": account_id}
                        for account_id, account in cls.data_source().accounts_autocomplete.accounts.items()
                    ],
                )
            )
        }

    @classmethod
    def year_start(cls):
        """Config flow set year start"""
        return {
            vol.Required(
                CONF_DATE_YEAR_START, default=cls.data_source().year_start
            ): selector.DateSelector()
        }

    @classmethod
    def month_start(cls):
        """Config flow set month start"""
        return {
            vol.Required(
                CONF_DATE_MONTH_START, default=cls.data_source().month_start
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=31,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            )
        }

    @classmethod
    def week_start(cls):
        """Config flow set week start"""
        return {
            vol.Required(
                CONF_DATE_WEEK_START, default=cls.data_source().week_start
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=WEEKDAYS,
                    translation_key=CONF_DATE_WEEK_START,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }

    @classmethod
    def lastx_time(cls):
        """Config flow set custum time"""
        lastx = cls.data_source().lastx_days
        lastx_back = lastx.get("back", 1)

        return {
            vol.Required(
                CONF_DATE_LASTX_BACK, default=lastx_back
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            )
        }

    @classmethod
    def lastx_type(cls):
        """Config flow set custum time type"""
        lastx = cls.data_source().lastx_days
        lastx_type = lastx.get("type")

        return {
            vol.Required(
                CONF_DATE_LASTX_BACK, default=lastx_type
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            )
        }

    @classmethod
    def schema_config(cls):
        """Config flow Schema config"""
        schema = {}

        if cls.data_source().get_categories:
            schema.update(cls.categories_ids())
        if cls.data_source().get_accounts:
            schema.update(cls.account_types())
            schema.update(cls.account_ids())

        if cls.data_source().is_date_range_year:
            schema.update(cls.year_start())
        elif cls.data_source().is_date_range_month:
            schema.update(cls.month_start())
        elif cls.data_source().is_date_range_week:
            schema.update(cls.week_start())
        elif cls.data_source().is_date_range_lastx:
            schema.update(cls.lastx_time())
            schema.update(cls.lastx_type())

        return vol.Schema(schema)

    @classmethod
    def schema_options(cls):
        """Config flow Schema options"""
        schema = {}

        schema.update(cls.url())
        schema.update(cls.access_token())

        return vol.Schema(schema)
