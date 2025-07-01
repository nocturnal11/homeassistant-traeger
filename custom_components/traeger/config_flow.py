"""Adds config flow for Blueprint."""

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import voluptuous as vol
import logging

from .traeger import traeger

from .const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_PELLET_OUTAGE_TEMP_DROP,
    CONF_PELLET_OUTAGE_TIME_THRESHOLD,
    DOMAIN,
    PLATFORMS,
    PELLET_OUTAGE_TEMP_DROP_F,
    PELLET_OUTAGE_TIME_THRESHOLD,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class BlueprintFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        user_input = {}
        # Provide defaults for form
        user_input[CONF_USERNAME] = ""
        user_input[CONF_PASSWORD] = ""

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BlueprintOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=user_input[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD, default=user_input[CONF_PASSWORD]): str,
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, username, password):
        """Return true if credentials is valid."""
        try:
            session = async_create_clientsession(self.hass)
            client = traeger(username, password, self.hass, session)
            await client.get_user_data()
            return True
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error(
                "Failed to login %s",
                exception,
            )
            pass
        return False


class BlueprintOptionsFlowHandler(config_entries.OptionsFlow):
    """Blueprint config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        # Create schema with platforms and pellet outage options
        schema_dict = {
            vol.Required(x, default=self.options.get(x, True)): bool
            for x in sorted(PLATFORMS)
        }

        # Add pellet outage configuration options
        schema_dict.update(
            {
                vol.Optional(
                    CONF_PELLET_OUTAGE_TEMP_DROP,
                    default=self.options.get(
                        CONF_PELLET_OUTAGE_TEMP_DROP, PELLET_OUTAGE_TEMP_DROP_F
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=20, max=100)),
                vol.Optional(
                    CONF_PELLET_OUTAGE_TIME_THRESHOLD,
                    default=self.options.get(
                        CONF_PELLET_OUTAGE_TIME_THRESHOLD, PELLET_OUTAGE_TIME_THRESHOLD
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=1800)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema_dict),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_USERNAME), data=self.options
        )
