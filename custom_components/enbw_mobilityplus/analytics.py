"""Charging analytics without Home Assistant dependencies."""

import hashlib
from datetime import datetime
from decimal import Decimal


def total(rows):
    def add(key):
        return float(sum((Decimal(str(r.get(key) or 0)) for r in rows), Decimal(0)))

    energy, cost = add("energy_in_kwh"), add("total_costs_in_eur")
    return {
        "count": len(rows),
        "energy": round(energy, 3),
        "cost": round(cost, 2),
        "blocking": round(add("blocking_fee_costs_in_eur"), 2),
        "discount": round(add("total_discount_in_eur"), 2),
        "price": round(cost / energy, 4) if energy else None,
    }


def station_key(row):
    # A station may contain several EVSEs; group by the provider's address/operator.
    identity = (
        row["operator"].strip().casefold() + "|" + " ".join(row["address"].casefold().split())
    )
    return hashlib.sha256(identity.encode()).hexdigest()[:16]


def summarize(history, now):
    rows = history["sessions"]
    months, years, stations = {}, {}, {}
    for row in rows:
        started = datetime.fromisoformat(row["started_at"].replace("Z", "+00:00"))
        if started.tzinfo is None:
            raise ValueError("Charging timestamp must include a timezone")
        local = started.astimezone(now.tzinfo)
        months.setdefault(local.strftime("%Y-%m"), []).append(row)
        years.setdefault(local.strftime("%Y"), []).append(row)
        key = station_key(row)
        if key not in stations:
            stations[key] = {
                "id": key,
                "address": row["address"],
                "operator": row["operator"],
                "latitude": row["location"]["latitude"],
                "longitude": row["location"]["longitude"],
                "evse_ids": set(),
                "rows": [],
            }
        stations[key]["evse_ids"].add(row["evse_id"])
        stations[key]["rows"].append(row)
    result_stations = []
    for station in stations.values():
        station_rows = station.pop("rows")
        station["evse_ids"] = sorted(station["evse_ids"])
        station.update(total(station_rows))
        station["last_visit"] = max(r["started_at"] for r in station_rows)
        result_stations.append(station)
    result_stations.sort(key=lambda s: (-s["count"], s["address"]))
    previous = now.replace(day=1)
    from datetime import timedelta

    previous -= timedelta(days=1)
    latest = rows[0] if rows else None
    return {
        "total": total(rows),
        "month": total(months.get(now.strftime("%Y-%m"), [])),
        "previous_month": total(months.get(previous.strftime("%Y-%m"), [])),
        "year": total(years.get(now.strftime("%Y"), [])),
        "months": [{"month": k, **total(v)} for k, v in sorted(months.items(), reverse=True)],
        "stations": result_stations,
        "station_count": len(result_stations),
        "average_power": round(latest["energy_in_kwh"] * 3600 / latest["duration_in_seconds"], 2)
        if latest and latest["duration_in_seconds"] > 0
        else None,
        "oldest": rows[-1]["started_at"] if rows else None,
    }
