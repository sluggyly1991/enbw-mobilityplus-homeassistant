"""Synthetic tariff scenarios; no account or location data."""

import importlib.util
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

spec = importlib.util.spec_from_file_location(
    "tariff", Path(__file__).parents[1] / "custom_components/enbw_mobilityplus/tariff.py"
)
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


class TariffTest(unittest.TestCase):
    def compare(self, volume, options=None, extra=None, limit=False):
        rows = [
            {
                "started_at": "2026-07-01T00:00:00Z",
                "energy_in_kwh": 1,
                "operator": "EnBW",
                "evse_id": "DE*EBW*TEST",
            }
        ]
        rows += [
            {
                "started_at": f"2026-{m:02}-15T12:00:00Z",
                "energy_in_kwh": volume,
                "operator": "EnBW",
                "evse_id": "DE*EBW*TEST",
            }
            for m in (8, 9, 10)
        ]
        return t.compare_tariffs(
            {"sessions": rows + (extra or []), "limit_reached": limit},
            datetime(2026, 11, 6, tzinfo=ZoneInfo("Europe/Berlin")),
            options,
        )

    def test_upgrade_m_l(self):
        r = self.compare(160, {"current_tariff": "M"})
        self.assertEqual(
            (r["recommendation"], r["target_tariff"], r["monthly_savings"]), ("Ja", "L", 5.2)
        )
        self.assertAlmostEqual(r["break_even_kwh"], 85.714, places=3)

    def test_downgrade_to_s(self):
        r = self.compare(10, {"current_tariff": "M"})
        self.assertEqual(
            (r["recommendation"], r["target_tariff"], r["direction"], r["monthly_savings"]),
            ("Ja", "S", "downgrade", 4.99),
        )
        self.assertEqual(r["threshold_relation"], "below")

    def test_downgrade_l_m(self):
        r = self.compare(70, {"current_tariff": "L"})
        self.assertEqual((r["target_tariff"], r["monthly_savings"]), ("M", 1.1))

    def test_current_best_and_equal(self):
        self.assertEqual(self.compare(70)["recommendation"], "Nein")
        self.assertEqual(self.compare(100, {"tariff_l_fee": 12.99})["recommendation"], "Nein")

    def test_s_can_skip_m(self):
        self.assertEqual(self.compare(200, {"current_tariff": "S"})["target_tariff"], "L")

    def test_zero_months_included(self):
        self.assertEqual(self.compare(0)["target_tariff"], "S")

    def test_foreign_and_roaming_excluded(self):
        extra = [
            {
                "started_at": "2026-10-20T12:00:00Z",
                "energy_in_kwh": 9999,
                "operator": operator,
                "evse_id": evse,
            }
            for operator, evse in [("Other", "DE*OTHER*1"), ("EnBW", "AT*EBW*1")]
        ]
        self.assertEqual(self.compare(70, extra=extra)["average_energy"], 70)

    def test_limits_and_invalid_prices(self):
        self.assertEqual(self.compare(70, limit=True)["reason"], "history_limit_reached")
        for value in (-1, float("nan"), float("inf")):
            self.assertEqual(
                self.compare(70, {"tariff_m_price": value})["reason"], "invalid_prices"
            )
        self.assertEqual(
            self.compare(70, {"tariff_prices_checked": "2026-09-01"})["reason"], "prices_outdated"
        )

    def test_short_and_bad_history(self):
        now = datetime(2026, 11, 6, tzinfo=ZoneInfo("Europe/Berlin"))
        self.assertEqual(
            t.compare_tariffs({"sessions": [], "limit_reached": False}, now)["recommendation"],
            "Prüfen",
        )
        self.assertEqual(
            self.compare(70, extra=[{"started_at": "bad", "energy_in_kwh": 10}])["reason"],
            "invalid_history",
        )

    def test_local_boundary_and_year_rollover(self):
        rows = [
            {"started_at": x, "energy_in_kwh": e, "operator": "EnBW", "evse_id": "DE*EBW*TEST"}
            for x, e in [
                ("2025-09-01T00:00:00Z", 0),
                ("2025-12-31T23:30:00Z", 300),
                ("2025-12-31T22:30:00Z", 30),
            ]
        ]
        r = t.compare_tariffs(
            {"sessions": rows, "limit_reached": False},
            datetime(2026, 1, 6, tzinfo=ZoneInfo("Europe/Berlin")),
            {"tariff_prices_checked": "2026-01-01"},
        )
        self.assertEqual(r["average_energy"], 10)
        self.assertEqual(r["current_month_energy"], 300)
        self.assertEqual(r["period_start"], "2025-10-01")
