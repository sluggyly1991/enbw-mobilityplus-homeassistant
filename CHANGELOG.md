# Changelog

## 0.4.0 — 2026-11-09

### Added

- S/M/L tariff comparison with configurable current tariff, monthly fees, charging prices and price-verification date. Compares upgrades and downgrades using the last three complete local calendar months.
- Decision, net monthly savings, break-even volume and average EnBW usage sensors. Incomplete history and stale tariff prices produce a check state instead of a guessed recommendation.
- Standalone color tariff card: green switch, blue stay, amber check/wait; combined costs and savings, light/dark themes, German/English text, expandable calculation details and configure/refresh actions.
- **Switched today** action (`enbw_mobilityplus.record_tariff_change`) and card control: records S/M/L and today's local date in Home Assistant only. Proposes the next date one calendar month later, including month-end/leap-year handling. Both dates are editable to match the EnBW app; the card distinguishes potential savings from an allowed switch date. No EnBW contract is changed.
- Local midnight comparison recalculation without extra API polling, 31 Python tests and 17 frontend input/state checks.

### Changed

- Included in the [HACS default catalog](https://github.com/hacs/default/pull/13490) on 9 November 2026.
- English/German READMEs now lead with **HACS search → EnBW mobility+ History**; the custom repository is retained as a fallback, as requested in the HACS review.
- Added card installation instructions, a synthetic-data preview and reusable dashboard examples.

### Upgrade notes

- Update the integration through HACS and restart Home Assistant; keep the existing integration entry and its settings.
- The optional color card is installed separately from `www/enbw-tariff-card.js`. Register `/local/enbw-tariff-card.js?v=0.4.0` as a JavaScript module and replace the example entity IDs. Updating the integration through HACS does not copy this file into `/config/www`.
- Select your actual S/M/L tariff in the integration options. Price defaults were checked on 6 November 2026 and need manual confirmation at least every 31 days. A recorded switch date and its proposed next date are reminders, not a guarantee of your EnBW contract terms.

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
