"""EnBW mobility+ charging history integration."""

import voluptuous as vol
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .api import Account
from .const import DOMAIN
from .coordinator import EnBWCoordinator
from .tariff import next_tariff_date

PLATFORMS = ["sensor", "button"]


async def async_setup_entry(hass, entry):
    coordinator = EnBWCoordinator(hass, entry, Account(entry.data["email"], entry.data["password"]))
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await coordinator.close()
        raise
    entry.runtime_data = coordinator
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        await coordinator.close()
        entry.runtime_data = None
        raise

    if not hass.services.has_service(DOMAIN, "get_history"):

        async def get_history(call):
            entries = [
                e
                for e in hass.config_entries.async_entries(DOMAIN)
                if getattr(e, "runtime_data", None) is not None
            ]
            entry_id = call.data.get("config_entry_id")
            if entry_id:
                entries = [e for e in entries if e.entry_id == entry_id]
            if len(entries) != 1:
                raise HomeAssistantError(
                    "Bitte genau ein geladenes EnBW-Konto über config_entry_id wählen"
                )
            return await entries[0].runtime_data.history(call.data["limit"])

        hass.services.async_register(
            DOMAIN,
            "get_history",
            get_history,
            schema=vol.Schema(
                {
                    vol.Optional("config_entry_id"): str,
                    vol.Optional("limit", default=1000): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=10000)
                    ),
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, "get_stations"):

        async def get_stations(call):
            entries = [
                e
                for e in hass.config_entries.async_entries(DOMAIN)
                if getattr(e, "runtime_data", None) is not None
            ]
            entry_id = call.data.get("config_entry_id")
            if entry_id:
                entries = [e for e in entries if e.entry_id == entry_id]
            if len(entries) != 1:
                raise HomeAssistantError("Bitte genau ein geladenes EnBW-Konto wählen")
            coordinator = entries[0].runtime_data
            return {
                "stations": [
                    {**s, **coordinator.station_live(s)} for s in coordinator.data["stations"]
                ],
                "limit_reached": coordinator.data["limit_reached"],
            }

        hass.services.async_register(
            DOMAIN,
            "get_stations",
            get_stations,
            schema=vol.Schema({vol.Optional("config_entry_id"): str}),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, "record_tariff_change"):

        async def record_tariff_change(call):
            entries = [
                e
                for e in hass.config_entries.async_entries(DOMAIN)
                if getattr(e, "runtime_data", None) is not None
            ]
            entry_id = call.data.get("config_entry_id")
            if entry_id:
                entries = [e for e in entries if e.entry_id == entry_id]
            if len(entries) != 1:
                raise HomeAssistantError("Bitte genau ein geladenes EnBW-Konto wählen")
            target = entries[0]
            today = dt_util.now().date()
            hass.config_entries.async_update_entry(
                target,
                options={
                    **target.options,
                    "current_tariff": call.data["tariff"],
                    "tariff_started_on": today.isoformat(),
                    "tariff_next_switch_on": next_tariff_date(today).isoformat(),
                },
            )

        hass.services.async_register(
            DOMAIN,
            "record_tariff_change",
            record_tariff_change,
            schema=vol.Schema(
                {
                    vol.Required("tariff"): vol.In(["S", "M", "L"]),
                    vol.Optional("config_entry_id"): str,
                }
            ),
        )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.close()
    entry.runtime_data = None
    if not any(
        getattr(e, "runtime_data", None) is not None
        for e in hass.config_entries.async_entries(DOMAIN)
    ):
        hass.services.async_remove(DOMAIN, "get_history")
        hass.services.async_remove(DOMAIN, "get_stations")
        hass.services.async_remove(DOMAIN, "record_tariff_change")
    return True
