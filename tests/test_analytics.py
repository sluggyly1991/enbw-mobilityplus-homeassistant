import importlib.util
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

spec = importlib.util.spec_from_file_location(
    "analytics", Path(__file__).parents[1] / "custom_components/enbw_mobilityplus/analytics.py"
)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def row(start, evse="DE*TEST*1", address="Teststraße 1", energy=10, cost=4):
    return {
        "started_at": start,
        "evse_id": evse,
        "address": address,
        "operator": "EnBW",
        "location": {"latitude": 51.0, "longitude": 7.0},
        "energy_in_kwh": energy,
        "total_costs_in_eur": cost,
        "duration_in_seconds": 1800,
        "blocking_fee_costs_in_eur": 0,
        "total_discount_in_eur": 0,
    }


class AnalyticsTest(unittest.TestCase):
    def run_summary(self, rows, date="2026-11-06T12:00:00"):
        return a.summarize(
            {"sessions": rows},
            datetime.fromisoformat(date).replace(tzinfo=ZoneInfo("Europe/Berlin")),
        )

    def test_local_month_boundary(self):
        s = self.run_summary([row("2026-10-31T23:30:00Z"), row("2026-10-31T22:30:00Z")])
        self.assertEqual(s["month"]["count"], 1)
        self.assertEqual(s["previous_month"]["count"], 1)
        self.assertEqual(s["year"]["count"], 2)

    def test_multiple_evses_same_station(self):
        rows = [row("2026-11-06T10:00:00Z", "A"), row("2026-11-05T10:00:00Z", "B")]
        s = self.run_summary(rows)
        self.assertEqual(s["station_count"], 1)
        self.assertEqual(s["stations"][0]["evse_ids"], ["A", "B"])
        self.assertEqual(s["stations"][0]["cost"], 8)
        self.assertEqual(a.station_key(rows[0]), a.station_key(rows[1]))

    def test_empty(self):
        s = self.run_summary([])
        self.assertEqual(s["month"]["energy"], 0)
        self.assertIsNone(s["month"]["price"])
        self.assertIsNone(s["average_power"])

    def test_weighted_price(self):
        s = self.run_summary(
            [
                row("2026-11-06T10:00:00Z", energy=10, cost=5),
                row("2026-11-05T10:00:00Z", energy=30, cost=9),
            ]
        )
        self.assertEqual(s["month"]["price"], 0.35)
        self.assertEqual(s["average_power"], 20)

    def test_previous_month_january(self):
        s = self.run_summary([row("2025-12-20T12:00:00Z")], date="2026-01-10T12:00:00")
        self.assertEqual(s["previous_month"]["count"], 1)
        self.assertEqual(s["year"]["count"], 0)

    def test_decimal_money(self):
        s = self.run_summary(
            [row("2026-11-06T10:00:00Z", cost=0.1), row("2026-11-05T10:00:00Z", cost=0.2)]
        )
        self.assertEqual(s["total"]["cost"], 0.3)
