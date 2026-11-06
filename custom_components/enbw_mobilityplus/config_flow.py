import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import Account, AuthenticationError
from .const import DOMAIN
from .tariff import DEFAULTS

PASSWORD = selector.TextSelector(
    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
)

SCHEMA = vol.Schema({vol.Required("email"): str, vol.Required("password"): PASSWORD})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlow()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            user_input = dict(user_input)
            user_input["email"] = user_input["email"].strip().lower()
            await self.async_set_unique_id(user_input["email"])
            self._abort_if_unique_id_configured()
            account = Account(user_input["email"], user_input["password"])

            def validate():
                try:
                    account.history(1)
                finally:
                    account.close()

            try:
                await self.hass.async_add_executor_job(validate)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="EnBW mobility+", data=user_input)
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        if user_input is not None:
            entry = self._get_reauth_entry()
            account = Account(entry.data["email"], user_input["password"])

            def validate():
                try:
                    account.history(1)
                finally:
                    account.close()

            try:
                await self.hass.async_add_executor_job(validate)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required("password"): PASSWORD}),
            errors=errors,
        )


class OptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "current_tariff",
                        default=self.config_entry.options.get("current_tariff", "M"),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["S", "M", "L"], mode=selector.SelectSelectorMode.DROPDOWN
                        )
                    ),
                    **{
                        vol.Required(
                            key, default=self.config_entry.options.get(key, value)
                        ): vol.All(vol.Coerce(float), vol.Range(min=0, max=200))
                        for key, value in DEFAULTS.items()
                        if key.startswith("tariff_") and key != "tariff_prices_checked"
                    },
                    vol.Required(
                        "tariff_prices_checked",
                        default=self.config_entry.options.get(
                            "tariff_prices_checked", DEFAULTS["tariff_prices_checked"]
                        ),
                    ): selector.DateSelector(),
                    **{
                        vol.Optional(
                            key,
                            description={"suggested_value": self.config_entry.options[key]}
                            if self.config_entry.options.get(key)
                            else {},
                        ): selector.DateSelector()
                        for key in ("tariff_started_on", "tariff_next_switch_on")
                    },
                    vol.Required(
                        "update_hours", default=self.config_entry.options.get("update_hours", 6)
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
                    vol.Required(
                        "history_limit",
                        default=self.config_entry.options.get("history_limit", 1000),
                    ): vol.All(vol.Coerce(int), vol.Range(min=25, max=10000)),
                }
            ),
        )
