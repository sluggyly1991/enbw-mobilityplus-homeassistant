# Changelog

## Unreleased

- Configurable S/M/L tariff comparison, including upgrades and downgrades, using the last three complete calendar months.
- Native reusable dashboard card: yes/no, best alternative, net monthly savings and break-even volume.
- Explicit coverage and price-age guards; configurable prices and verification date.
- Local midnight recalculation without extra API polling; synthetic comparison tests.

## 0.3.0

First public Home Assistant release, prepared for HACS custom-repository installation and default-catalog review.

- Preserves upstream client history and MIT attribution; adds Home Assistant integration ownership and repository links.
- HACS manifest, local brand assets, HACS/hassfest workflows and offline tests on Python 3.12–3.14.
- English/German installation, privacy, troubleshooting, dashboard and contributor documentation.
- Buy Me a Coffee support link for sluggyly1991.
- Count-only diagnostics; separate authentication errors in the setup form; cleanup after platform setup failures.
- Retains entity unique IDs from the locally tested 0.2.0 integration.

## 0.2.0

- Month, previous month, year and captured-history totals.
- Latest charging details and calculated average power.
- Map-ready visited stations grouped by address/operator.
- Exact EVSE-ID matching to existing live availability sensors.
- Configurable update interval and history limit; manual refresh button.
- History/station response actions and recent-session attributes excluded from Recorder.

## 0.1.0

- Initial Home Assistant config flow, coordinator and latest-charge sensors.

The original client's changelog remains in the upstream Git history. Its package version and integration release versions are independent.
