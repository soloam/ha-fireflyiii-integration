"""FireflyIII Integration Coordinator"""

import logging
from calendar import monthrange
from datetime import datetime, timedelta

from datetimerange import DateTimeRange
from homeassistant import config_entries
from homeassistant.const import WEEKDAYS
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .fireflyiii import Fireflyiii
from .fireflyiii_config import FireflyiiiConfig
from .fireflyiii_objects import FireflyiiiObjectBaseList

_LOGGER = logging.getLogger(__name__)


class FireflyiiiCoordinator(DataUpdateCoordinator):
    """FireflyIII coordinator class"""

    def __init__(self, hass, interval, entry: config_entries.ConfigEntry):
        """Initialize."""
        self.interval = timedelta(seconds=interval)
        self._entry = entry
        self._hass = hass

        self._user_data = FireflyiiiConfig(self._entry.data)
        self._user_data.update(self._entry.options)

        self.name = f"FireflyIII ({self.user_data.name})"

        self._api = Fireflyiii(
            self.user_data.host,
            self.user_data.access_token,
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
    def timerange(self) -> DateTimeRange | None:
        """Return defined timerange"""

        timerange = None

        reference = datetime.today()

        if self.user_data.is_date_range_year or self.user_data.is_date_range_last_year:
            if self.user_data.is_date_range_last_year:
                reference = reference.replace(year=reference.year - 1)

            year_start_date_str = self.user_data.year_start

            try:
                year_start_date = datetime.strptime(year_start_date_str, "%Y-%m-%d")
            except ValueError:
                year_start_date = reference.replace(
                    year=reference.year,
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

            if year_start_date > reference:
                year_end_date = year_start_date - timedelta(microseconds=1)

                year_start_date = year_start_date.replace(year=year_start_date.year - 1)
            else:
                year_end_date = year_start_date.replace(
                    year=year_start_date.year + 1
                ) - timedelta(microseconds=1)

            timerange = DateTimeRange(year_start_date, year_end_date)

        elif (
            self.user_data.is_date_range_month
            or self.user_data.is_date_range_last_month
        ):
            if self.user_data.is_date_range_last_month:
                last_month = reference.replace(day=1) - timedelta(days=1)
                reference = self._set_day_bound(last_month, reference.day)

            month_start_day = self.user_data.month_start

            date_ref = self._set_day_bound(reference, month_start_day)

            if date_ref > reference:
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
        elif (
            self.user_data.is_date_range_week or self.user_data.is_date_range_last_week
        ):
            if self.user_data.is_date_range_last_week:
                reference = reference - timedelta(weeks=1)

            week_start_day_str = self.user_data.week_start

            date_ref = reference.replace(hour=0, minute=0, second=0, microsecond=0)

            try:
                week_start_day = WEEKDAYS.index(week_start_day_str)
            except ValueError:
                week_start_day = 0

            week_end_date = self._set_next_weekday(week_start_day, date_ref)
            week_start_date = week_end_date - timedelta(weeks=1)
            week_end_date = week_end_date - timedelta(microseconds=1)

            timerange = DateTimeRange(week_start_date, week_end_date)
        elif self.user_data.is_date_range_day or self.user_data.is_date_range_yesterday:
            if self.user_data.is_date_range_last_week:
                reference = reference - timedelta(days=1)

            day_start_date = reference.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end_date = reference.replace(
                hour=23, minute=59, second=59, microsecond=59
            )

            timerange = DateTimeRange(day_start_date, day_end_date)
        elif self.user_data.is_date_range_lastx:
            try:
                lastx_number = int(self.user_data.lastx_days.get("back", 1))
            except ValueError:
                lastx_number = 1

            keys_date = {"years": 0, "weeks": 0, "days": 0}

            if self.user_data.is_lastx_days_type_years:
                keys_date["weeks"] = lastx_number * 52
            elif self.user_data.is_lastx_days_type_weeks:
                keys_date["weeks"] = lastx_number
            elif self.user_data.is_lastx_days_type_days:
                keys_date["days"] = lastx_number

            date_ref = reference.replace(hour=0, minute=0, second=0, microsecond=0)

            lastx_start_date = date_ref - timedelta(
                days=keys_date["days"], weeks=keys_date["weeks"]
            )
            lastx_end_date = date_ref.replace(
                hour=23, minute=59, second=59, microsecond=59
            )

            timerange = DateTimeRange(lastx_start_date, lastx_end_date)

        if timerange:
            return timerange

        return None

    @property
    def user_data(self) -> FireflyiiiConfig:
        """Return User input config flow data"""
        return self._user_data

    @property
    def api(self) -> Fireflyiii:
        """Return FireflyIII api"""
        return self._api

    @property
    def api_data(self) -> FireflyiiiObjectBaseList:
        """Return API Returned data from coordinator"""
        return self.data

    async def _async_update_data(self):
        """Run coordinator update"""

        data_list = FireflyiiiObjectBaseList()

        data_list.update(self.api.about())
        data_list.update(self.api.preferences())

        if self.user_data.get_accounts:
            data_list.update(
                self.api.accounts(
                    types=self.user_data.account_types, ids=self.user_data.account_ids
                )
            )

        if self.user_data.get_categories:
            data_list.update(self.api.categories(ids=self.user_data.categories_ids))

        if self.user_data.get_bills:
            data_list.update(self.api.bills())

        if self.user_data.get_piggy_banks:
            data_list.update(self.api.piggy_banks())

        if self.user_data.get_budgets:
            data_list.update(self.api.budgets())

        await data_list.gather()
        return data_list
