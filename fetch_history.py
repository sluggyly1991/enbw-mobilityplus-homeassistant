#!/usr/bin/env python3
"""Standalone JSON export. Credentials are requested interactively, never via argv."""

import argparse
import getpass
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="EnBW-Ladehistorie als JSON abrufen")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=Path("ladehistorie.json"))
    args = parser.parse_args()
    if not 1 <= args.limit <= 10000:
        parser.error("--limit muss zwischen 1 und 10000 liegen")
    spec = importlib.util.spec_from_file_location(
        "enbw_api", Path(__file__).parent / "custom_components/enbw_mobilityplus/api.py"
    )
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    account = api.Account(input("EnBW E-Mail: ").strip(), getpass.getpass("EnBW Passwort: "))
    try:
        result = account.history(args.limit)
        # Exclusive creation protects existing exports; private file permissions.
        import os

        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as target:
            json.dump(result, target, ensure_ascii=False, indent=2)
        print(f"{len(result['sessions'])} Ladevorgänge gespeichert: {args.output}")
        if result["limit_reached"]:
            print("Abrufgrenze erreicht; gegebenenfalls --limit erhöhen.")
    except Exception:
        raise SystemExit(
            "Abruf/Export fehlgeschlagen. Anmeldung, Verbindung und Ausgabepfad prüfen."
        ) from None
    finally:
        account.close()


if __name__ == "__main__":
    main()
