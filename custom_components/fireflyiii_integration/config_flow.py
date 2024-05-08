"""FireflyIII Integration Config Flow"""

import logging
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow

from .const import DOMAIN
from .integrations.fireflyiii_config import FireflyiiiConfig, FireflyiiiConfigSchema

# from homeassistant.core import callback


_LOGGER = logging.getLogger(__name__)


class FireflyiiiConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore
    """FireflyIII Integration config flow."""

    VERSION = 1
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

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Reconfig Flow"""
        errors: Dict[str, str] = {}
        if user_input is not None:
            entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
            old_data = entry.data.copy()
            old_data.update(user_input)
            fireflyiii_config = FireflyiiiConfig(old_data)
            fireflyiii_api = await fireflyiii_config.get_api()

            if not await fireflyiii_api.check_connection():
                errors["base"] = "auth"

            if not errors:
                self.data = fireflyiii_config
                FireflyiiiConfigSchema.set_data_source(self.data)

                return self.async_show_form(
                    step_id="reconfigure2",
                    data_schema=FireflyiiiConfigSchema.schema_reconfigure2(),
                    errors=errors,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=FireflyiiiConfigSchema.schema_reconfigure(),
            errors=errors,
        )

    async def async_step_reconfigure2(self, user_input: dict[str, Any] | None = None):
        """Reconfig Flow"""
        errors: Dict[str, str] = {}
        if user_input is not None:
            entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
            self.data.update(user_input)

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    title=self.data.name,
                    data=self.data,
                    reason="reconfigure_successful",
                )

        return self.async_show_form(
            step_id="reconfigure2",
            data_schema=FireflyiiiConfigSchema.schema_reconfigure2(),
            errors=errors,
        )

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     """Get the options flow for this handler."""
    #     return OptionsFlowHandler(config_entry)


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

        await FireflyiiiConfigSchema.data_source().get_api()

        if user_input is not None:
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=FireflyiiiConfigSchema.schema_options(),
            errors=errors,
        )
