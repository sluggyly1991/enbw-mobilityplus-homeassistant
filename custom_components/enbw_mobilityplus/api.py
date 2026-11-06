"""Synchronous adapter; always run in Home Assistant's executor."""

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


class AuthenticationError(Exception):
    """The account needs to sign in again."""


class Account:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.client = None

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def login(self):
        from enbw_mobilityplus_client import EnBWMobilityPlusClient

        self.close()
        self.client = EnBWMobilityPlusClient()
        try:
            self.client.login(self.email, self.password)
        except ValueError:
            self.close()
            raise AuthenticationError("EnBW login failed") from None
        except Exception:
            self.close()
            raise

    def history(self, limit=25):
        if self.client is None:
            self.login()
        try:
            return fetch_history(self.client, limit)
        except ValueError as err:
            # Upstream reports HTTP errors as ValueError, not HTTPStatusError.
            if not re.search(r": (?:401|403)\b", str(err)):
                raise
            if self.client.refresh_token:
                try:
                    self.client.refresh_access_token()
                except ValueError:
                    raise AuthenticationError("EnBW token refresh failed") from None
            else:
                self.login()
            try:
                return fetch_history(self.client, limit)
            except ValueError as retry_error:
                if re.search(r": (?:401|403)\b", str(retry_error)):
                    raise AuthenticationError("EnBW authentication rejected") from None
                raise
