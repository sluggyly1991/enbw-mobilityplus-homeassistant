"""Latest charge, period totals and visited stations."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

PARALLEL_UPDATES = 0

LATEST = [
    ("energy_in_kwh", "Letzte Ladung Energie", "kWh", SensorDeviceClass.ENERGY),
    ("total_costs_in_eur", "Letzte Ladung Kosten", "EUR", SensorDeviceClass.MONETARY),
    ("started_at", "Letzte Ladung Beginn", None, SensorDeviceClass.TIMESTAMP),
    ("duration_in_seconds", "Letzte Ladung Dauer", "s", SensorDeviceClass.DURATION),
    ("charging_price_per_kwh_in_cent", "Letzte Ladung Preis", "ct/kWh", None),
    (
        "blocking_fee_costs_in_eur",
        "Letzte Ladung Blockiergebuehr",
        "EUR",
        SensorDeviceClass.MONETARY,
    ),
    ("total_discount_in_eur", "Letzte Ladung Rabatt", "EUR", SensorDeviceClass.MONETARY),
    ("operator", "Letzte Ladung Betreiber", None, None),
    ("address", "Letzte Ladung Ort", None, None),
    ("charge_plug_type", "Letzte Ladung Steckertyp", None, None),
]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    entities = [
        EnBWSensor(coordinator, entry.entry_id, key, name, unit, dc, "latest")
        for key, name, unit, dc in LATEST
    ]
    for scope, label in [
        ("month", "Monat"),
        ("previous_month", "Vormonat"),
        ("year", "Jahr"),
        ("total", "Erfasste Historie"),
    ]:
        for key, name, unit, dc in [
            ("energy", "Energie", "kWh", SensorDeviceClass.ENERGY),
            ("cost", "Kosten", "EUR", SensorDeviceClass.MONETARY),
            ("count", "Ladungen", None, None),
            ("price", "Durchschnittspreis", "EUR/kWh", None),
        ]:
            entities.append(
                EnBWSensor(coordinator, entry.entry_id, key, f"{label} {name}", unit, dc, scope)
            )
    entities.extend(
        [
            EnBWSensor(
                coordinator,
                entry.entry_id,
                "average_power",
                "Letzte Ladung Durchschnittsleistung",
                "kW",
                SensorDeviceClass.POWER,
                "root",
            ),
            EnBWSensor(
                coordinator,
                entry.entry_id,
                "station_count",
                "Besuchte Stationen",
                None,
                None,
                "root",
            ),
            EnBWSensor(
                coordinator,
                entry.entry_id,
                "updated_at",
                "Letzte Aktualisierung",
                None,
                SensorDeviceClass.TIMESTAMP,
                "root",
            ),
            EnBWSensor(coordinator, entry.entry_id, "history", "Ladehistorie", None, None, "root"),
        ]
    )
    for key, name, unit, device_class in [
        ("recommendation", "Tarifwechsel", None, None),
        ("monthly_savings", "Tarifwechsel Ersparnis", "EUR", SensorDeviceClass.MONETARY),
        ("break_even_kwh", "Tarifwechsel Wechselgrenze", "kWh", SensorDeviceClass.ENERGY),
        ("average_energy", "Tarifwechsel Monatsverbrauch", "kWh", SensorDeviceClass.ENERGY),
    ]:
        entities.append(
            EnBWSensor(coordinator, entry.entry_id, key, name, unit, device_class, "tariff")
        )
    async_add_entities(entities)
    known = set()

    def add_stations():
        new = [s for s in coordinator.data["stations"] if s["id"] not in known]
        known.update(s["id"] for s in new)
        if new:
            async_add_entities([StationSensor(coordinator, entry.entry_id, s) for s in new])

    add_stations()
    entry.async_on_unload(coordinator.async_add_listener(add_stations))


class EnBWSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _unrecorded_attributes = frozenset({"sessions", "stations", "months"})

    def __init__(self, coordinator, entry_id, key, name, unit, device_class, scope):
        super().__init__(coordinator)
        self.key, self.scope = key, scope
        # Preserve all four original unique IDs.
        suffix = key if scope == "latest" else f"{scope}_{key}"
        self._attr_unique_id = f"{entry_id}_{suffix}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "EnBW mobility+",
            "manufacturer": "EnBW",
        }
        if scope == "tariff":
            self._attr_icon = "mdi:calculator-variant"
        if key in ("history", "station_count"):
            self._attr_icon = "mdi:ev-station" if key == "station_count" else "mdi:history"

    @property
    def native_value(self):
        data = self.coordinator.data
        if self.scope == "latest":
            value = data["sessions"][0].get(self.key) if data["sessions"] else None
        elif self.key == "history":
            value = len(data["sessions"])
        elif self.scope == "root":
            value = data[self.key]
        else:
            value = data[self.scope][self.key]
        if self._attr_device_class == SensorDeviceClass.TIMESTAMP:
            return dt_util.parse_datetime(value) if value else None
        return value

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if self.scope == "tariff":
            return data["tariff"]
        if self.scope == "latest":
            if not data["sessions"] or self.key != "started_at":
                return None
            row = data["sessions"][0]
            return {
                **{k: row[k] for k in ("address", "operator", "evse_id", "stopped_at")},
                "authentication": row["auth_identifier"].get("charge_auth_type"),
            }
        attrs = {
            "history_limit_reached": data["limit_reached"],
            "oldest_session": data["oldest"],
            "period_basis": "session_start_local_time",
        }
        if self.key == "history":
            fields = (
                "started_at",
                "stopped_at",
                "address",
                "operator",
                "evse_id",
                "energy_in_kwh",
                "total_costs_in_eur",
                "charging_price_per_kwh_in_cent",
                "duration_in_seconds",
                "charge_plug_type",
            )
            attrs["sessions"] = [
                {
                    **{k: r[k] for k in fields},
                    "authentication": r["auth_identifier"].get("charge_auth_type"),
                }
                for r in data["sessions"][:50]
            ]
            attrs["display_limit"] = 50
            attrs["months"] = data["months"]
        if self.key == "station_count":
            attrs["stations"] = [
                {**s, **self.coordinator.station_live(s)} for s in data["stations"]
            ]
        return attrs


class StationSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:ev-station"
    _unrecorded_attributes = frozenset({"live_charge_points"})

    def __init__(self, coordinator, entry_id, station):
        super().__init__(coordinator)
        self.station_id = station["id"]
        self._attr_unique_id = f"{entry_id}_station_{self.station_id}"
        self._attr_name = f"Station {station['address']}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "EnBW mobility+",
            "manufacturer": "EnBW",
        }
        self._attr_native_unit_of_measurement = "Ladungen"

    @property
    def station(self):
        return next(
            (s for s in self.coordinator.data["stations"] if s["id"] == self.station_id), None
        )

    @property
    def available(self):
        return super().available and self.station is not None

    @property
    def native_value(self):
        return self.station["count"] if self.station else None

    @property
    def extra_state_attributes(self):
        station = self.station
        return {**station, **self.coordinator.station_live(station)} if station else None
