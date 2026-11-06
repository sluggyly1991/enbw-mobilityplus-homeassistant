# Native dashboard examples

These examples use placeholder entity IDs. Replace every ID with one from your account device before adding a card through the dashboard editor's YAML mode. Do not paste them into `configuration.yaml`. Existing areas and language settings may produce different entity IDs.

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
