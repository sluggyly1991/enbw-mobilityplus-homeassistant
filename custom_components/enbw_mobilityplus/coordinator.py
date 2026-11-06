import asyncio
import logging
from datetime import timedelta

from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .analytics import summarize
from .api import AuthenticationError
from .const import DOMAIN
from .tariff import compare_tariffs


class EnBWCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, account):
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(hours=entry.options.get("update_hours", 6)),
        )
        self.account = account
        self.lock = asyncio.Lock()
        self.entry = entry
        self.live = {}
        self._remove_tariff_clock = async_track_time_change(
            hass, self._refresh_tariff, hour=0, minute=0, second=5
        )
        for state in hass.states.async_all("sensor"):
            self._remember_live(state)
        self._remove_live = hass.bus.async_listen("state_changed", self._live_changed)

    async def history(self, limit):
        async with self.lock:
            try:
                return await self.hass.async_add_executor_job(self.account.history, limit)
            except AuthenticationError:
                raise ConfigEntryAuthFailed("EnBW-Anmeldung erneuern") from None
            except Exception:
                # Upstream exception messages may contain response bodies or auth URLs.
                raise UpdateFailed(
                    "EnBW-Abruf fehlgeschlagen; Verbindung und Anmeldung prüfen"
                ) from None

    def _remember_live(self, state):
        if state is None:
            return
        attrs = state.attributes
        # Only station availability entities, never our own historical EVSE attributes.
        if attrs.get("evse_id") and "AVAILABLE" in attrs.get("options", []):
            self.live[state.entity_id] = {
                "entity_id": state.entity_id,
                "evse_id": attrs["evse_id"],
                "state": state.state,
                "max_power_kw": attrs.get("max_power_kw"),
                "plug_types": attrs.get("plug_types", []),
                "status_changed_at": attrs.get("status_changed_at"),
            }

    @callback
    def _live_changed(self, event):
        entity_id = event.data.get("entity_id")
        state = event.data.get("new_state")
        before = dict(self.live)
        self.live.pop(entity_id, None)
        self._remember_live(state)
        if before != self.live and self.data is not None:
            self.async_update_listeners()

    def station_live(self, station):
        points = [p for p in self.live.values() if p["evse_id"] in station["evse_ids"]]
        return {
            "live_charge_points": points,
            "monitored_charge_points": len(points),
            "available_charge_points": sum(p["state"] == "AVAILABLE" for p in points),
            "live_coverage": "historical_evse_only",
        }

    @callback
    def _refresh_tariff(self, now):
        if self.data is not None:
            self.data["tariff"] = compare_tariffs(self.data, dt_util.now(), self.entry.options)
            self.async_update_listeners()

    async def _async_update_data(self):
        history = await self.history(self.entry.options.get("history_limit", 1000))
        return {
            **history,
            **summarize(history, dt_util.now()),
            "tariff": compare_tariffs(history, dt_util.now(), self.entry.options),
            "updated_at": dt_util.utcnow().isoformat(),
        }

    async def close(self):
        self._remove_live()
        self._remove_tariff_clock()
        async with self.lock:
            await self.hass.async_add_executor_job(self.account.close)
