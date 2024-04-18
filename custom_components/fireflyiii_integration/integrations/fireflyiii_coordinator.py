"""FireflyIII Integration Coordinator"""

import logging
from asyncio import gather
from calendar import monthrange
from datetime import datetime, timedelta

from datetimerange import DateTimeRange
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_URL
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..const import (
    CONF_DATE_LASTX_BACK,
    CONF_DATE_LASTX_BACK_TYPE,
    CONF_DATE_LASTX_BACK_TYPES,
    CONF_DATE_LASTX_DAYS_TYPE,
    CONF_DATE_LASTX_WEEKS_TYPE,
    CONF_DATE_LASTX_YEARS_TYPE,
    CONF_DATE_MONTH_START,
    CONF_DATE_WEEK_START,
    CONF_DATE_YEAR_START,
    CONF_RETURN_ACCOUNT_TYPE,
    CONF_RETURN_ACCOUNTS,
    CONF_RETURN_CATEGORIES,
    CONF_RETURN_RANGE,
    CONF_RETURN_RANGE_DAY_TYPE,
    CONF_RETURN_RANGE_LASTX_TYPE,
    CONF_RETURN_RANGE_MONTH_TYPE,
    CONF_RETURN_RANGE_WEEK_TYPE,
    CONF_RETURN_RANGE_YEAR_TYPE,
    FIREFLYIII_ACCOUNT_SENSOR_TYPE,
    FIREFLYIII_CATEGORY_SENSOR_TYPE,
    WEEKDAYS,
)
from .fireflyiii import Fireflyiii

_LOGGER = logging.getLogger(__name__)


class FireflyiiiCoordinator(DataUpdateCoordinator):
    """FireflyIII coordinator class"""

    def __init__(self, hass, interval, entry: config_entries.ConfigEntry):
        """Initialize."""
        self.interval = timedelta(seconds=interval)
        self._entry = entry
        self.name = f"FireflyIII ({self.user_data.get(CONF_NAME)})"
        self._hass = hass
        self._data = {}

        self._api = Fireflyiii(
            self.user_data.get(CONF_URL),
            self.user_data.get(CONF_ACCESS_TOKEN),
            self.timerange,
        )

        _LOGGER.debug("Data will be update every %s", self.interval)
        super().__init__(hass, _LOGGER, name=self.name, update_interval=self.interval)

    def _set_day_bound(self, date: datetime, day, reset=True) -> datetime:
        (_, last_day) = monthrange(year=date.year, month=date.month)

        if day < 1:
            day = 1
        elif day > last_day:
            day = last_day

        date_new = date.replace(day=day)
        if reset:
            date_new = date_new.replace(hour=0, minute=0, second=0, microsecond=0)
        return date_new

    def _set_next_month(self, date: datetime, reset=True):
        (_, last_day) = monthrange(year=date.year, month=date.month)

        date_new = date.replace(day=last_day) + timedelta(hours=24)
        date_new = self._set_day_bound(date_new, date.day, reset)
        return date_new

    def _set_next_weekday(self, weekday: int, date: datetime) -> datetime:
        if weekday == date.weekday():
            return date + timedelta(days=7)
        elif weekday > date.weekday():
            return date + timedelta(days=weekday - date.weekday())
        return (date - timedelta(days=date.weekday())) + timedelta(days=weekday + 7)

    @property
    def timerange(self) -> dict:
        """Return defined timerange"""

        timerange = None

        if self.user_data.get(CONF_RETURN_RANGE) == CONF_RETURN_RANGE_YEAR_TYPE:
            default = f"{datetime.today().year}-01-01"
            year_start_date = self.user_data.get(CONF_DATE_YEAR_START, default)

            try:
                year_start_date = datetime.strptime(year_start_date, "%Y-%m-%d")
            except ValueError:
                year_start_date = datetime.today().replace(
                    year=datetime.today().year,
                    month=1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

            year_start_date = year_start_date.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            if year_start_date > datetime.today():
                year_end_date = year_start_date - timedelta(microseconds=1)

                year_start_date = year_start_date.replace(year=year_start_date.year - 1)
            else:
                year_end_date = year_start_date.replace(
                    year=year_start_date.year + 1
                ) - timedelta(microseconds=1)

            timerange = DateTimeRange(year_start_date, year_end_date)

        elif self.user_data.get(CONF_RETURN_RANGE) == CONF_RETURN_RANGE_MONTH_TYPE:
            month_start_day = int(self.user_data.get(CONF_DATE_MONTH_START, 1))

            date_ref = self._set_day_bound(datetime.today(), month_start_day)

            if date_ref > datetime.today():
                date_start = date_ref - timedelta(days=date_ref.day + 7)
                date_start = self._set_day_bound(date_start, month_start_day)
                date_end = self._set_day_bound(date_ref, (month_start_day - 1)).replace(
                    hour=23, minute=59, second=59, microsecond=59
                )
            else:
                date_start = date_ref
                date_end = self._set_next_month(date_ref)
                date_end = self._set_day_bound(date_end, month_start_day) - timedelta(
                    microseconds=1
                )

            timerange = DateTimeRange(date_start, date_end)
        elif self.user_data.get(CONF_RETURN_RANGE) == CONF_RETURN_RANGE_WEEK_TYPE:
            week_start_day = self.user_data.get(CONF_DATE_WEEK_START, WEEKDAYS[0])

            date_ref = datetime.today().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            try:
                week_start_day = WEEKDAYS.index(week_start_day)
            except ValueError:
                week_start_day = 0

            week_end_date = self._set_next_weekday(week_start_day, date_ref)
            week_start_date = week_end_date - timedelta(weeks=1)
            week_end_date = week_end_date - timedelta(microseconds=1)

            timerange = DateTimeRange(week_start_date, week_end_date)
        elif self.user_data.get(CONF_RETURN_RANGE) == CONF_RETURN_RANGE_DAY_TYPE:
            day_start_date = datetime.today().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end_date = datetime.today().replace(
                hour=23, minute=59, second=59, microsecond=59
            )

            timerange = DateTimeRange(day_start_date, day_end_date)
        elif self.user_data.get(CONF_RETURN_RANGE) == CONF_RETURN_RANGE_LASTX_TYPE:
            try:
                lastx_number = self.user_data.get(CONF_DATE_LASTX_BACK, 1)
            except ValueError:
                lastx_number = 1

            lastx_type = self.user_data.get(
                CONF_DATE_LASTX_BACK_TYPE, CONF_DATE_LASTX_BACK_TYPES[0]
            )

            if lastx_type not in CONF_DATE_LASTX_BACK_TYPES:
                lastx_type = CONF_DATE_LASTX_BACK_TYPES[0]

            keys_date = {}

            if lastx_type == CONF_DATE_LASTX_YEARS_TYPE:
                keys_date["years"] = lastx_number
            elif lastx_type == CONF_DATE_LASTX_WEEKS_TYPE:
                keys_date["weeks"] = lastx_number
            elif lastx_type == CONF_DATE_LASTX_DAYS_TYPE:
                keys_date["days"] = lastx_number

            date_ref = datetime.today().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            lastx_start_date = date_ref - timedelta(**keys_date)
            lastx_end_date = date_ref.replace(
                hour=23, minute=59, second=59, microsecond=59
            )

            timerange = DateTimeRange(lastx_start_date, lastx_end_date)

        if timerange:
            return timerange

    @property
    def user_data(self) -> dict:
        """Return User input config flow data"""
        return self._entry.data

    @property
    def api(self) -> Fireflyiii:
        """Return FireflyIII api"""
        return self._api

    @property
    def api_data(self) -> dict:
        """Return API Returned data from coordinator"""
        return self._data

        # self.parse_sensors()

    async def _async_update_data(self):
        """Run coordinator update"""

        data = {}
        data["about"] = self.api.about()
        # if self._data["about"]:
        #     self._data["version"] = self._data["about"]["version"]
        #     self._data["os"] = self._data["about"]["os"]

        data["start_year"] = self.api.start_year

        if (
            CONF_RETURN_ACCOUNTS in self.user_data
            and self.user_data[CONF_RETURN_ACCOUNTS]
        ):
            data[FIREFLYIII_ACCOUNT_SENSOR_TYPE] = self.api.accounts(
                types=self.user_data.get(CONF_RETURN_ACCOUNT_TYPE, [])
            )

        if (
            CONF_RETURN_CATEGORIES in self.user_data
            and self.user_data[CONF_RETURN_CATEGORIES]
        ):
            data[FIREFLYIII_CATEGORY_SENSOR_TYPE] = self.api.categories()

        data["default_currency"] = self.api.default_currency

        results = await gather(*[res for res in data.values()])

        data_keys = data.keys()

        for inx, key in enumerate(data_keys):
            data[key] = results[inx]

        self._data = data
