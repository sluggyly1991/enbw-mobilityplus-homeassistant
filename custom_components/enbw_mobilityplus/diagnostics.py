"""Diagnostics intentionally contain no account, session or location data."""

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    data = coordinator.data if coordinator is not None else None
    return {
        "options": {
            "update_hours": entry.options.get("update_hours", 6),
            "history_limit": entry.options.get("history_limit", 1000),
        },
        "last_update_success": coordinator.last_update_success if coordinator else None,
        "session_count": len(data["sessions"]) if data else 0,
        "station_count": data["station_count"] if data else 0,
        "history_limit_reached": data["limit_reached"] if data else None,
    }
