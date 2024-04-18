"""FireflyIII Integration Config Flow"""

import logging
from typing import Any, Dict, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_DATE_LASTX_BACK,
    CONF_DATE_LASTX_BACK_TYPE,
    CONF_DATE_LASTX_BACK_TYPES,
    CONF_DATE_MONTH_START,
    CONF_DATE_WEEK_START,
    CONF_DATE_YEAR_START,
    CONF_NAME,
    CONF_NAME_DEFAULT,
    CONF_RETURN_ACCOUNT_ID,
    CONF_RETURN_ACCOUNT_TYPE,
    CONF_RETURN_ACCOUNT_TYPE_DEFAULT,
    CONF_RETURN_ACCOUNT_TYPES,
    CONF_RETURN_ACCOUNTS,
    CONF_RETURN_ACCOUNTS_DEFAULT,
    CONF_RETURN_BUDGETS,
    CONF_RETURN_BUDGETS_DEFAULT,
    CONF_RETURN_CATEGORIES,
    CONF_RETURN_CATEGORIES_DEFAULT,
    CONF_RETURN_CATEGORIES_ID,
    CONF_RETURN_INVOICES,
    CONF_RETURN_INVOICES_DEFAULT,
    CONF_RETURN_PIGGY_BANKS,
    CONF_RETURN_PIGGY_BANKS_DEFAULT,
    CONF_RETURN_RANGE,
    CONF_RETURN_RANGE_DAY_TYPE,
    CONF_RETURN_RANGE_DEFAULT,
    CONF_RETURN_RANGE_LASTX_TYPE,
    CONF_RETURN_RANGE_MONTH_TYPE,
    CONF_RETURN_RANGE_TYPES,
    CONF_RETURN_RANGE_WEEK_TYPE,
    CONF_RETURN_RANGE_YEAR_TYPE,
    CONF_URL,
    DOMAIN,
    WEEKDAYS,
)

try:

    from .const_dev import (  # pyright: ignore[reportMissingImports]
        CONF_ACCESS_TOKEN_DEFAULT,
        CONF_URL_DEFAULT,
    )
except ModuleNotFoundError as err:
    CONF_ACCESS_TOKEN_DEFAULT = ""
    CONF_URL_DEFAULT = ""

from .integrations.fireflyiii import Fireflyiii

# from homeassistant.helpers.entity_registry import async_get


_LOGGER = logging.getLogger(__name__)

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=CONF_NAME_DEFAULT): cv.string,
        vol.Required(CONF_ACCESS_TOKEN, default=CONF_ACCESS_TOKEN_DEFAULT): cv.string,
        vol.Required(CONF_URL, default=CONF_URL_DEFAULT): cv.string,
    }
)
SENSORS_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_RETURN_BUDGETS, default=CONF_RETURN_BUDGETS_DEFAULT
        ): cv.boolean,
        vol.Optional(
            CONF_RETURN_INVOICES, default=CONF_RETURN_INVOICES_DEFAULT
        ): cv.boolean,
        vol.Optional(
            CONF_RETURN_PIGGY_BANKS, default=CONF_RETURN_PIGGY_BANKS_DEFAULT
        ): cv.boolean,
        vol.Optional(
            CONF_RETURN_CATEGORIES, default=CONF_RETURN_CATEGORIES_DEFAULT
        ): cv.boolean,
        vol.Optional(
            CONF_RETURN_ACCOUNTS, default=CONF_RETURN_ACCOUNTS_DEFAULT
        ): cv.boolean,
        vol.Required(
            CONF_RETURN_RANGE, default=CONF_RETURN_RANGE_DEFAULT
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=CONF_RETURN_RANGE_TYPES,
                translation_key=CONF_RETURN_RANGE,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)

# vol.Optional(CONF_START_DATE): selector.DateSelector(),
# vol.Optional(CONF_END_DATE): selector.DateSelector(),


OPTIONS_SHCEMA = vol.Schema({vol.Optional(CONF_NAME, default="foo"): cv.string})


class FireflyiiiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """FireflyIII Integration config flow."""

    VERSION = 2
    MINOR_VERSION = 0

    data: Optional[Dict[str, Any]]

    fireflyiii = None

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:

            self.fireflyiii = Fireflyiii(
                user_input[CONF_URL], user_input[CONF_ACCESS_TOKEN]
            )

            if not await self.fireflyiii.check_connection():
                errors["base"] = "auth"

            if not errors:
                # Input is valid, set data.
                self.data = user_input
                # Return the form of the next step.
                return await self.async_step_sensors()

        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        )

    @staticmethod
    async def get_config_schema(data: dict, fireflyiii_api: Fireflyiii):
        """Generates config schema"""
        schema = {}

        if data[CONF_RETURN_CATEGORIES]:
            schema[vol.Optional(CONF_RETURN_CATEGORIES_ID)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    multiple=True, custom_value=True, options=[]
                )
            )

        if data[CONF_RETURN_ACCOUNTS]:
            schema[
                vol.Required(
                    CONF_RETURN_ACCOUNT_TYPE,
                    default=CONF_RETURN_ACCOUNT_TYPE_DEFAULT,
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=CONF_RETURN_ACCOUNT_TYPES,
                    translation_key=CONF_RETURN_ACCOUNT_TYPE,
                    multiple=True,
                )
            )

            schema[vol.Optional(CONF_RETURN_ACCOUNT_ID)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    multiple=True,
                    custom_value=True,
                    options=[],
                )
            )

            # accounts = await self.fireflyiii.accounts

            # lst_accounts = [
            #     accounts[account]["attributes"]["name"] for account in accounts
            # ]

            # schema[vol.Required("Teste")] = selector.SelectSelector(
            #     selector.SelectSelectorConfig(
            #         options=lst_accounts,
            #         multiple=True,
            #         mode=selector.SelectSelectorMode.DROPDOWN,
            #     )
            # )

        if data[CONF_RETURN_RANGE] == CONF_RETURN_RANGE_YEAR_TYPE:
            schema[
                vol.Required(
                    CONF_DATE_YEAR_START,
                    default=await fireflyiii_api.start_year,
                )
            ] = selector.DateSelector()
        elif data[CONF_RETURN_RANGE] == CONF_RETURN_RANGE_MONTH_TYPE:
            schema[vol.Required(CONF_DATE_MONTH_START, default=1)] = (
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=31,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )
            )
        elif data[CONF_RETURN_RANGE] == CONF_RETURN_RANGE_WEEK_TYPE:
            schema[vol.Required(CONF_DATE_WEEK_START)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=WEEKDAYS,
                    translation_key=CONF_DATE_WEEK_START,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        elif data[CONF_RETURN_RANGE] == CONF_RETURN_RANGE_DAY_TYPE:
            pass
        elif data[CONF_RETURN_RANGE] == CONF_RETURN_RANGE_LASTX_TYPE:
            schema[vol.Required(CONF_DATE_LASTX_BACK, default=1)] = (
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )
            )

            schema[vol.Required(CONF_DATE_LASTX_BACK_TYPE)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=CONF_DATE_LASTX_BACK_TYPES,
                    translation_key=CONF_DATE_LASTX_BACK_TYPE,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )

        return vol.Schema(schema)

    async def async_step_sensors(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add sensors to return"""
        errors: Dict[str, str] = {}
        if user_input is not None:

            self.data.update(user_input)

            if not errors:
                data_schema = await FireflyiiiConfigFlow.get_config_schema(
                    self.data, self.fireflyiii
                )

                return self.async_show_form(
                    step_id="config", data_schema=data_schema, errors=errors
                )

        return self.async_show_form(
            step_id="sensors", data_schema=SENSORS_SCHEMA, errors=errors
        )

    async def async_step_config(self, user_input: Optional[Dict[str, Any]] = None):
        """Third step in config flow to add config."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            self.data.update(user_input)

            title = self.data[CONF_NAME] or CONF_NAME_DEFAULT

            if not errors:
                return self.async_create_entry(title=title, data=self.data)

        return self.async_show_form(
            step_id="config",
            data_schema=self.cur_step.data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

        self.fireflyiii = Fireflyiii(
            self.config_entry.data[CONF_URL], self.config_entry.data[CONF_ACCESS_TOKEN]
        )

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}

        # entity_registry = async_get(self.hass)
        # entries = async_entries_for_config_entry(
        #    entity_registry, self.config_entry.entry_id
        # )

        if user_input is not None:
            pass
            # if not errors:
            #     return self.async_create_entry(
            #         title="",
            #         data={CONF_REPOS: updated_repos},
            #     )

        options_schema = await FireflyiiiConfigFlow.get_config_schema(
            self.config_entry.data, self.fireflyiii
        )
        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )
