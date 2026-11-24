import importlib.util
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location(
    "api", Path(__file__).parents[1] / "custom_components/enbw_mobilityplus/api.py"
)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class Session:
    def __init__(self, n):
        self.n = n

    def model_dump(self, **kwargs):
        return dict(
            evse_id=str(self.n),
            started_at="2026-11-01T10:00:00Z",
            stopped_at="2026-11-01T11:00:00Z",
        )


class Client:
    def __init__(self, count):
        self.rows = [Session(n) for n in range(count)]
        self.calls = []

    def get_charging_history(self, limit, offset):
        self.calls.append((limit, offset))
        return self.rows[offset : offset + limit]


class HistoryTest(unittest.TestCase):
    def test_pagination(self):
        client = Client(61)
        result = api.fetch_history(client, 100)
        self.assertEqual(len(result["sessions"]), 61)
        self.assertFalse(result["limit_reached"])
        self.assertEqual(client.calls, [(25, 0), (25, 25), (25, 50), (25, 75)])

    def test_exact_bound(self):
        client = Client(100)
        result = api.fetch_history(client, 31)
        self.assertEqual(len(result["sessions"]), 31)
        self.assertTrue(result["limit_reached"])
        self.assertEqual(client.calls, [(25, 0), (6, 25)])

    def test_empty(self):
        self.assertEqual(api.fetch_history(Client(0)), {"sessions": [], "limit_reached": False})

    def test_ignored_offset_fails(self):
        client = Client(25)
        client.get_charging_history = lambda limit, offset: client.rows
        with self.assertRaisesRegex(ValueError, "advance"):
            api.fetch_history(client)

    def test_failed_login_closes_client(self):
        import sys
        from types import SimpleNamespace

        class BrokenClient:
            closed = False

            def login(self, *args):
                raise ValueError("failure")

            def close(self):
                self.closed = True

        client = BrokenClient()
        account = api.Account("email", "password")
        with patch.dict(
            sys.modules,
            {"enbw_mobilityplus_client": SimpleNamespace(EnBWMobilityPlusClient=lambda: client)},
        ):
            with self.assertRaises(api.APIError) as raised:
                account.login()
            self.assertNotIsInstance(raised.exception, api.AuthenticationError)
        self.assertTrue(client.closed)
        self.assertIsNone(account.client)

    def test_overlap_at_limit_is_flagged(self):
        client = Mock()
        client.get_charging_history.side_effect = [
            [Session(n) for n in range(25)],
            [Session(24), Session(25)],
        ]
        result = api.fetch_history(client, 27)
        self.assertEqual(len(result["sessions"]), 26)
        self.assertTrue(result["limit_reached"])

    def test_invalid_limit(self):
        for limit in (0, 10001):
            with self.assertRaises(ValueError):
                api.fetch_history(Client(0), limit)

    def test_token_refresh_and_retry(self):
        client = Mock(refresh_token="old-refresh")
        client.get_charging_history.side_effect = [
            ValueError("Failed to get charging history: 401 - private"),
            [Session(1)],
        ]
        account = api.Account("email", "password")
        account.client = client
        result = account.history(1)
        self.assertEqual(len(result["sessions"]), 1)
        client.refresh_access_token.assert_called_once()

    def test_retry_auth_error_is_sanitized(self):
        client = Mock(refresh_token="refresh")
        client.get_charging_history.side_effect = ValueError(
            "Failed to get charging history: 401 - PRIVATE_TOKEN"
        )
        account = api.Account("email", "password")
        account.client = client
        with self.assertRaises(api.AuthenticationError) as raised:
            account.history(1)
        self.assertNotIn("PRIVATE_TOKEN", str(raised.exception))
        self.assertTrue(raised.exception.__suppress_context__)

    def test_transient_error_does_not_refresh(self):
        client = Mock(refresh_token="refresh")
        client.get_charging_history.side_effect = ValueError("Failed to get charging history: 503")
        account = api.Account("email", "password")
        account.client = client
        with self.assertRaises(api.APIError):
            account.history(1)
        client.refresh_access_token.assert_not_called()

    def test_login_failure_categories(self):
        cases = [
            ("Login failed: 401", api.AuthenticationError, "Zugangsdaten"),
            ("Login failed: 403", api.APIError, "Zugriffsschutz"),
            ("Login failed: 429", api.APIError, "begrenzt"),
            ("Authorization failed: 503", api.APIError, "vorübergehend"),
            (
                "Could not extract authorization code. Status: 200, URL: SECRET",
                api.APIError,
                "Login-Ablauf",
            ),
            (
                'Token refresh failed: 400 - {"error":"invalid_grant"}',
                api.AuthenticationError,
                "Anmeldung erneuern",
            ),
            (
                'Token refresh failed: 400 - {"error":"invalid_request"}',
                api.APIError,
                "API/Login-Ablauf",
            ),
            ("Response body: 401 SECRET", api.APIError, "Datenformat"),
        ]
        for message, expected, text in cases:
            with self.subTest(message=message):
                error = api.classify_error(ValueError(message), "Anmeldung")
                self.assertIs(type(error), expected)
                self.assertIn(text, str(error))
                self.assertNotIn("SECRET", str(error))

    def test_network_failure_categories(self):
        self.assertIn(
            "Zeitüberschreitung", str(api.classify_error(TimeoutError("SECRET"), "Anmeldung"))
        )
        self.assertIn("Verbindung", str(api.classify_error(OSError("SECRET"), "Anmeldung")))

    def test_logs_never_include_upstream_details(self):
        account = api.Account("PRIVATE_EMAIL", "PRIVATE_PASSWORD")
        operation = Mock(
            side_effect=ValueError("Login failed: 403 - PRIVATE_TOKEN https://private")
        )
        with self.assertLogs("api", level="WARNING") as logs:
            with self.assertRaises(api.APIError) as raised:
                account._call(operation, "Anmeldung")
        self.assertIn("HTTP 403", logs.output[0])
        self.assertNotIn("PRIVATE", str(logs.output))
        self.assertNotIn("https://", str(logs.output))
        self.assertTrue(raised.exception.__suppress_context__)

    def test_transient_refresh_failure_does_not_require_reauth(self):
        client = Mock(refresh_token="refresh")
        client.get_charging_history.side_effect = ValueError("Failed to get charging history: 401")
        client.refresh_access_token.side_effect = ValueError("Token refresh failed: 503 - PRIVATE")
        account = api.Account("email", "password")
        account.client = client
        with self.assertRaises(api.APIError) as raised:
            account.history(1)
        self.assertNotIsInstance(raised.exception, api.AuthenticationError)
        self.assertIn("503", str(raised.exception))

    def test_history_body_cannot_trigger_refresh(self):
        client = Mock(refresh_token="refresh")
        client.get_charging_history.side_effect = ValueError(
            "Failed to get charging history: 503 - error: 401"
        )
        account = api.Account("email", "password")
        account.client = client
        with self.assertRaises(api.APIError):
            account.history(1)
        client.refresh_access_token.assert_not_called()

    def test_close_is_idempotent(self):
        account = api.Account("email", "password")
        client = Mock()
        account.client = client
        account.close()
        account.close()
        client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
