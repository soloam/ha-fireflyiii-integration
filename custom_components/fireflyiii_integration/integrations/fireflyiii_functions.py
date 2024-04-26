"""Useful functions"""

from datetime import datetime
from typing import Optional

from babel import Locale, UnknownLocaleError
from babel.numbers import LC_NUMERIC, format_currency
from datetimerange import DateTimeRange
from homeassistant.core import HomeAssistant

from .fireflyiii_objects import FireflyiiiCurrency


def get_locale(language: str, territory: Optional[str] = None) -> str:
    """Get The Locale"""
    try:
        locale = Locale(language, territory=territory)
    except UnknownLocaleError:
        try:
            locale = Locale(language)
        except UnknownLocaleError:
            return ""

    return str(locale)


def get_hass_locale(hass: HomeAssistant) -> str:
    """Returns Hass Locale"""
    return get_locale(hass.config.language, territory=hass.config.country)


def output_money(
    value: float, currency: str | FireflyiiiCurrency, locale: str | None = LC_NUMERIC
) -> str:
    """Output Monetary Data With Unit"""

    if isinstance(currency, FireflyiiiCurrency):
        target_currency = str(currency)
    else:
        target_currency = currency

    try:
        value = float(value)
    except ValueError:
        value = 0

    return format_currency(value, target_currency, locale=locale)


def dates_to_range(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> DateTimeRange:
    """Returns Date Time Range"""

    if not start_date:
        start_date = datetime.now()

    if not end_date:
        end_date = datetime.now()

    start_date_timed = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date_timed = end_date.replace(hour=23, minute=59, second=59, microsecond=59)

    timerange = DateTimeRange(start_date_timed, end_date_timed)
    return timerange
