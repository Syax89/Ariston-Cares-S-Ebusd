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
- zone day/night temperatures and setpoint bundle (validated from dump analysis)

What is still experimental / unverified:

- thermoreg parameters (offset, slope, min/max water temp) - NOT seen in Cares S dumps
- diagnostic flag blocks (`d3..de` families)
- exact meaning of some zone-state bytes

What is still being refined:

- exact meaning of some zone-state bytes
- diagnostic flag blocks (`d3..de` families)
- final interpretation of a few heating-related logical flags

## Recommended files

- Main config: [`aris.csv`](aris.csv)
- Shared templates: [`_templates.csv`](_templates.csv)
- Reverse-engineering summary: [`reverse_engineering_report.json`](reverse_engineering_report.json)

## Installation

Copy `aris.csv` and `_templates.csv` into your `ebusd` config path.

Example:

```bash
ebusd --scanconfig=0 --configpath=/etc/ebusd --device=/dev/ttyUSB0
```

For ENS/TCP adapters:

```bash
ebusd --scanconfig=0 --configpath=/config/Ariston --device=ens:192.168.4.74:9999
```

`--scanconfig=0` is recommended so `ebusd` does not load generic Ariston CSV files instead of this one.

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
- `outdoor_temperature_bc = 3276.7` typically means raw `ff7f`, i.e. invalid / sensor absent
- `current_power_level` now looks much more credible than in the first iterations, because it changes under real load

For the full reverse-engineering state, use [`reverse_engineering_report.json`](reverse_engineering_report.json).

## Contributing

If you want to help, the most useful contributions are:

- new `pcapng` captures
- raw `ebusd` log snippets
- notes describing what physically changed on the boiler during the capture

## License

MIT License.
