"""FireflyIII Integration Config Flow"""

import logging
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback

from .const import DOMAIN
from .integrations.fireflyiii_config import FireflyiiiConfig, FireflyiiiConfigSchema

_LOGGER = logging.getLogger(__name__)


class FireflyiiiConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore
    """FireflyIII Integration config flow."""

    VERSION = 2
    MINOR_VERSION = 0

    data: FireflyiiiConfig

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:

            fireflyiii_config = FireflyiiiConfig(user_input)
            fireflyiii_api = await fireflyiii_config.get_api()

            if not await fireflyiii_api.check_connection():
                errors["base"] = "auth"

            if not errors:
                # Input is valid, set data.
                self.data = fireflyiii_config
                FireflyiiiConfigSchema.set_data_source(fireflyiii_config)
                # Return the form of the next step.
                return await self.async_step_sensors()

        return self.async_show_form(
            step_id="user",
            data_schema=FireflyiiiConfigSchema.schema_auth(),
            errors=errors,
        )

    async def async_step_sensors(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add sensors to return"""
        errors: Dict[str, str] = {}
        if user_input is not None:

            self.data.update(user_input)

            if not errors:
                return self.async_show_form(
                    step_id="config",
                    data_schema=FireflyiiiConfigSchema.schema_config(),
                    errors=errors,
                )

        return self.async_show_form(
            step_id="sensors",
            data_schema=FireflyiiiConfigSchema.schema_sensor(),
            errors=errors,
        )

    async def async_step_config(self, user_input: Optional[Dict[str, Any]] = None):
        """Third step in config flow to add config."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            self.data.update(user_input)

            if not errors:
                return self.async_create_entry(title=self.data.name, data=self.data)

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


class OptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry
        self._old_config = FireflyiiiConfig(self.config_entry.data)
        self._old_config.update(self.config_entry.options)
        FireflyiiiConfigSchema.set_data_source(self._old_config)

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=FireflyiiiConfigSchema.schema_options(),
            errors=errors,
        )
