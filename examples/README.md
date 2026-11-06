# Native dashboard examples

These examples use placeholder entity IDs. Replace every ID with one from your account device before adding a card through the dashboard editor's YAML mode. Do not paste them into `configuration.yaml`. Existing areas and language settings may produce different entity IDs.

## Color tariff card (unreleased / main)

See the [README installation steps](../README.md#color-tariff-card-unreleased--main). After registering the local module, use [tariff-color-card.yaml](tariff-color-card.yaml) and replace its two entity IDs. All information and actions are contained in this one card. Its decision uses color **and text/icons**: green switch, blue stay, amber check. The plain Markdown alternative remains available below.

## Monthly overview

```yaml
type: grid
columns: 2
square: false
cards:
  - type: tile
    entity: sensor.replace_with_month_energy
    name: This month · energy
  - type: tile
    entity: sensor.replace_with_month_cost
    name: This month · cost
  - type: tile
    entity: sensor.replace_with_month_count
    name: Charging sessions
    icon: mdi:counter
  - type: tile
    entity: sensor.replace_with_month_effective_price
    name: Effective price
    icon: mdi:cash
```

## Visited stations map

Add the station sensor entities from this integration. Each carries latitude/longitude attributes. Add newly visited station entities to the map when they appear.

```yaml
type: map
entities:
  - entity: sensor.replace_with_visited_station
    label_mode: state
hours_to_show: 0
```

## Latest sessions

Set `history` below to the actual **Charging history / Ladehistorie** sensor. Its attributes contain at most 50 recent sessions. The `e` filter escapes provider text used in the table.

```yaml
type: markdown
content: |
  {% set history = 'sensor.replace_with_charging_history' %}
  {% set rows = state_attr(history, 'sessions') or [] %}
  {% if not has_value(history) %}
  Charging history is unavailable. Check the integration.
  {% elif not rows %}
  No charging sessions yet.
  {% else %}
  | Date / location | kWh | EUR |
  | :--- | ---: | ---: |
  {% for r in rows %}
  | **{{ as_timestamp(r.started_at) | timestamp_custom('%d.%m.%y %H:%M', true) }}**<br>{{ r.address | e }} | {{ '%.1f' | format(r.energy_in_kwh) }} | {{ '%.2f' | format(r.total_costs_in_eur) }} |
  {% endfor %}
  {% endif %}
```

## Linked availability

A station sensor exposes `monitored_charge_points`, `available_charge_points` and `live_charge_points`. Check `monitored_charge_points > 0` before showing availability. Without live coverage, do not show a misleading "0 free".

```yaml
type: markdown
content: |
  {% set station = 'sensor.replace_with_visited_station' %}
  {% set monitored = state_attr(station, 'monitored_charge_points') | int(0) %}
  {% if not has_value(station) %}
  Station history unavailable.
  {% elif monitored > 0 %}
  {{ state_attr(station, 'available_charge_points') }} / {{ monitored }} matched charging points available.
  {% else %}
  No live availability sensors linked to this station.
  {% endif %}
```

The public availability integration's own station-total and individual-point entities can be placed beside this map/history. Their refresh interval remains independent of the history integration.

## Tariff comparison card (unreleased / main)

Copy [tariff-card.yaml](tariff-card.yaml) into **Add card → Manual** and replace its single placeholder with your integration's **Tarifwechsel** sensor. It is a native Markdown card; no frontend resource, JavaScript card or extra HACS download is needed. It shows **Wechseln: Ja/Nein**, upgrade/downgrade direction, best alternative, monthly costs, net saving and break-even volume.

Choose your actual **S, M or L tariff** under **Settings → Devices & services → EnBW mobility+ → Configure**. All three monthly fees and charging prices are editable, alongside their verification date. Defaults are regular German S/M/L prices verified on 2026-11-06; partner discounts must be entered manually. Prices expire after 31 days until confirmed again. The API does not supply a supported tariff catalogue or your contract selection.

The comparison uses **all fetched sessions**, not the 50-session display attribute, over three complete local calendar months (including zero-use months). It excludes roaming and foreign EVSEs. A record at/before the period start and a non-truncated response are required as a conservative coverage check. An archive silently shortened by the provider cannot be detected. Prices and future usage are assumptions, not a promise of savings. Already paid sessions are not repriced. The configured polling interval refreshes history; local midnight also rolls the comparison window forward without an extra API request. No subscription is changed.

Numeric sensors expose net savings (positive = alternative cheaper), break-even kWh and average monthly EnBW volume. The decision sensor returns **Prüfen**, and numerical values are unknown, when coverage or tariff prices cannot support a recommendation. Integration outages make the sensors unavailable.
