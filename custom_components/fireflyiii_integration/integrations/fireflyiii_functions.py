"""Useful functions"""

from babel import Locale, UnknownLocaleError
from babel.numbers import LC_NUMERIC, format_currency
from homeassistant.core import HomeAssistant
from typing import Optional


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


def output_money(value: float, currency: str, locale: str | None = LC_NUMERIC) -> str:
    """Output Monetary Data With Unit"""
    try:
        value = float(value)
    except ValueError:
        value = 0

    return format_currency(value, currency, locale=locale)
