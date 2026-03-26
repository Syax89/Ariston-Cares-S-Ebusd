# Ariston Cares S eBUSd Configuration

[![GitHub Release](https://img.shields.io/github/v/release/Syax89/Ariston-Cares-S-Ebusd?style=for-the-badge)](https://github.com/Syax89/Ariston-Cares-S-Ebusd/releases)
[![ebusd](https://img.shields.io/badge/ebusd-Compatible-blue?style=for-the-badge)](https://github.com/john30/ebusd)

Reverse-engineered `ebusd` configuration for **Ariston Cares S** boilers and closely related Galileo-platform models.

This project started as a custom `aris.csv` to make an Ariston Cares S usable with `ebusd`, and evolved into a dump-driven reverse-engineering effort based on:

- real packet captures (`dump.pcapng`, `dump2.pcapng`, `dump3.pcapng`)
- live validation through `ebusd`
- MQTT observation during real boiler activity

## Project goal

The goal is simple:

- map as many Ariston eBUS messages as possible
- keep only the rows that are logically validated
- expose useful entities for MQTT / Home Assistant
- document what is confirmed, what is usable, and what is still experimental

## Current status

The repository is already usable in practice.

What is working well right now:

- boiler operating mode
- request/status groups
- DHW setpoint and DHW actual temperature
- heating setpoint broadcasts
- main flow / return / exhaust / auxiliary temperatures
- pressure sensor voltage and pump modulation
- room and zone setpoints
- zone day/night temperatures and setpoint bundle (validated from dumps and live MQTT)
- secondary `200e` setpoint tables for comfort / reduced / antifreeze modes
- stable passive thermoreg families on branches `71/73/75`, plus structured hidden branches `72/74/76`

What is still experimental / unverified:

- exact semantics of some hidden-profile fields in the `2020` families, especially bridge/selector sidecars
- diagnostic flag blocks (`d3..de` families)
- exact meaning of some zone-state bytes

What is still being refined:

- exact meaning of some zone-state bytes
- diagnostic flag blocks (`d3..de` families)
- final interpretation of a few heating-related logical flags

## Recommended files

- Production config: [`aris.csv`](aris.csv)
- Development config: [`aris-development.csv`](aris-development.csv)
- Shared templates: [`_templates.csv`](_templates.csv)
- Reverse-engineering summary: [`json/reverse_engineering_report.json`](json/reverse_engineering_report.json)

Current evidence snapshot from the archived logs and MQTT exports:

- `confirmed: 37`
- `usable: 134`
- `candidate: 9`
- `unknown: 13`

## Installation

For normal use, copy `aris.csv` and `_templates.csv` into your `ebusd` config path.

Use `aris-development.csv` only when you want the exploratory layout with candidate rows, extended reverse-engineering notes, and partially decoded families. If you want to test it with `ebusd`, rename it to `aris.csv` in your config path.

Example:

```bash
ebusd --scanconfig=0 --configpath=/etc/ebusd --device=/dev/ttyUSB0
```

For ENS/TCP adapters:

```bash
ebusd --scanconfig=0 --configpath=/config/Ariston --device=ens:192.168.4.74:9999
```

`--scanconfig=0` is recommended so `ebusd` does not load generic Ariston CSV files instead of this one.

The production file intentionally excludes rows that are still useful for research but not yet clean enough for a stable day-to-day setup.

## Best entities to watch first

If you just want the most useful MQTT entities first, start with:

- `boiler_operating_mode`
- `flame_state`
- `request_status_1`
- `dhw_setpoint`
- `dhw_actual_temperature`
- `zone1_current_setpoint_bc`
- `zone1_day_temperature_bc`
- `zone1_night_temperature_bc` (polled via 200e, not broadcast)
- `zone1_setpoint_bundle_bc`
- `zone1_secondary_comfort_bc`
- `zone1_secondary_reduced_bc`
- `zone1_secondary_antifreeze_bc`
- `heating_setpoint_triplet`
- `internal_flow_target_temperature`
- `main_flow_temperature`
- `current_power_level`

## Validation philosophy

This repository does not treat a frame as valid just because it decodes once.

A row is promoted only when it is supported by one or more of these:

- repeated appearance across multiple dumps
- temporal consistency with real user actions
- plausible numeric range and unit
- confirmation from live `ebusd` logs

That is why some rows are active, some are documented as usable, and others remain commented or experimental.

## Technical notes

Some useful conclusions already established:

- `request_status_1` is the strongest heating-demand indicator found so far
- `dhw_setpoint` and `zone1_current_setpoint_bc` were validated by real setpoint changes
- `zone1_setpoint_bundle_bc` is now confirmed live in MQTT as `base_setpoint=5.0`, `day_temp=21.0`, `night_temp=16.0`
- `zone1_current_setpoint_bc` is now confirmed live in ebusd logs at `65.0`
- `status_request_1_flags` is now structurally confirmed and remains stable at `0 / 0 / 2 / 145` in recent passive captures
- `zone1_state_triplet_bc` now decodes live as `on;0;15`, so the third field is not a boolean
- `heating_active_bc` can reach `15`, so it should be treated as a status-like raw field, not a pure on/off sensor
- `fan_speed_raw` tracks burner activity, but values like `45569/49153/49921/52737` are not credible physical RPM yet
- the thermoreg family `6071/6171/6471/6a71/c079/c279` is now visible live in the `2020` broadcast family, and the current CSV keeps only evidence-backed fields active
- newer `200e` triples around `6272..6276`, `6372..6376`, and `6426` are stable across recent passive logs and currently decode best as `19.0/10.0/30.0`, `16.0/10.0/30.0`, and `5.0/2.0/15.0`
- those newer `200e` triples align with the `2020/0b` lookup rows, so they are currently treated as secondary comfort/reduced/antifreeze setpoint tables with trailing mode/profile metadata
- hidden thermoreg branches `72/74/76` now publish stable MQTT payloads too, including sidecars decoded as `basic_on_off ; 194 ; 122/124/126`
- corrected room-influence rows on branches `73/75` now publish real payloads `5.0 ; basic_on_off ; 10` instead of staying `unknown`
- `outdoor_temperature_bc = 3276.7` typically means raw `ff7f`, i.e. invalid / sensor absent
- `current_power_level` now looks much more credible than in the first iterations, because it changes under real load

For the full reverse-engineering state, use [`json/reverse_engineering_report.json`](json/reverse_engineering_report.json).

## Contributing

If you want to help, the most useful contributions are:

- new `pcapng` captures
- raw `ebusd` log snippets
- notes describing what physically changed on the boiler during the capture

## License

MIT License.
