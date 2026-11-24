"""Synchronous adapter; always run in Home Assistant's executor."""

import json
import logging
import re
from datetime import datetime


def fetch_history(client, max_entries=1000):
    """Fetch bounded pages, preserve distinct sessions and detect ignored offsets."""
    if not 1 <= max_entries <= 10000:
        raise ValueError("History limit must be between 1 and 10000")
    rows = []
    seen = set()
    limit_reached = True
    for offset in range(0, max_entries, 25):
        page = client.get_charging_history(limit=min(25, max_entries - offset), offset=offset)
        if not page:
            limit_reached = False
            break
        added = 0
        for session in page:
            row = session.model_dump(mode="json")
            key = (row["evse_id"], row["started_at"], row["stopped_at"])
            if key not in seen:
                seen.add(key)
                rows.append(row)
                added += 1
        if not added:
            raise ValueError("Pagination did not advance")
    rows.sort(
        key=lambda r: datetime.fromisoformat(r["started_at"].replace("Z", "+00:00")), reverse=True
    )
    return {"sessions": rows, "limit_reached": limit_reached}


_LOGGER = logging.getLogger(__name__)


class APIError(Exception):
    """A safe, categorized failure without upstream response content."""


class AuthenticationError(APIError):
    """The account needs to sign in again."""


def classify_error(error, phase):
    """Only explicit authentication rejection warrants a reauthentication flow."""
    message = str(error)
    match = re.match(
        r"^(Authorization failed|Identifier submission failed|Failed to load password page|"
        r"Login failed|Token exchange failed|Token refresh failed|Failed to get profiles|"
        r"Failed to get charging history): ([1-5][0-9]{2})(?=$|[ -])",
        message,
    )
    status = int(match[2]) if match else None
    if match and match[1] == "Login failed" and status == 401:
        return AuthenticationError(
            "EnBW hat die Anmeldung abgelehnt (HTTP 401); Zugangsdaten prüfen"
        )
    if match and match[1] in ("Token refresh failed", "Token exchange failed"):
        # A 400 alone can also mean a changed request format. Only invalid_grant
        # explicitly identifies a rejected/expired authorization grant.
        try:
            body = json.loads(message.split(" - ", 1)[1])
        except (IndexError, ValueError):
            body = None
        if isinstance(body, dict) and body.get("error") == "invalid_grant":
            return AuthenticationError("EnBW hat den Anmeldetoken abgelehnt; Anmeldung erneuern")
    if status == 429:
        return APIError("EnBW begrenzt die Anfragen (HTTP 429); später erneut versuchen")
    if status is not None and status >= 500:
        return APIError(f"EnBW-Dienst vorübergehend nicht verfügbar (HTTP {status})")
    if status == 403:
        return APIError(
            "EnBW verweigert den Zugriff (HTTP 403); Zugriffsschutz oder Login-Ablauf prüfen"
        )
    if status is not None:
        return APIError(
            f"EnBW-Anfrage bei {phase} abgelehnt (HTTP {status}); API/Login-Ablauf prüfen"
        )
    if isinstance(error, TimeoutError) or type(error).__name__ in {
        "ConnectTimeout",
        "ReadTimeout",
        "WriteTimeout",
        "PoolTimeout",
    }:
        return APIError(f"Zeitüberschreitung bei EnBW ({phase}); Verbindung oder Dienst prüfen")
    if isinstance(error, OSError) or type(error).__name__ in {
        "ConnectError",
        "ReadError",
        "WriteError",
        "RemoteProtocolError",
        "ProxyError",
    }:
        return APIError(f"Verbindung zu EnBW fehlgeschlagen ({phase}); Netzwerk oder Dienst prüfen")
    if isinstance(error, ValueError):
        return APIError(
            f"Unerwartete EnBW-Antwort bei {phase}; Login-Ablauf oder Datenformat möglicherweise geändert"
        )
    return APIError(
        f"Unerwarteter interner Fehler bei {phase}; Integration und Client-Version prüfen"
    )


class Account:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.client = None

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def _call(self, operation, phase):
        try:
            return operation()
        except APIError:
            raise
        except Exception as error:
            safe_error = classify_error(error, phase)
            # Never log raw exceptions, traceback, URLs, credentials or bodies.
            _LOGGER.warning("%s", safe_error)
            raise safe_error from None

    def login(self):
        from enbw_mobilityplus_client import EnBWMobilityPlusClient

        self.close()
        self.client = EnBWMobilityPlusClient()
        try:
            self._call(lambda: self.client.login(self.email, self.password), "Anmeldung")
        except Exception:
            self.close()
            raise

    def history(self, limit=25):
        if self.client is None:
            self.login()
        try:
            return self._fetch_history(limit)
        except APIError:
            raise
        except Exception as error:
            safe_error = classify_error(error, "Ladehistorie")
            _LOGGER.warning("%s", safe_error)
            raise safe_error from None

    def _fetch_history(self, limit):
        try:
            return fetch_history(self.client, limit)
        except ValueError as error:
            # Match the upstream status prefix, never numbers in a response body.
            if not re.match(r"^Failed to get charging history: (?:401|403)(?=$|[ -])", str(error)):
                raise
        if self.client.refresh_token:
            self._call(self.client.refresh_access_token, "Token-Erneuerung")
        else:
            self.login()
        try:
            return fetch_history(self.client, limit)
        except ValueError as error:
            if re.match(r"^Failed to get charging history: 401(?=$|[ -])", str(error)):
                safe_error = AuthenticationError(
                    "EnBW lehnt den Zugriff auch nach Token-Erneuerung ab (HTTP 401); Anmeldung erneuern"
                )
                _LOGGER.warning("%s", safe_error)
                raise safe_error from None
            raise
