# Ariston Cares S ebusd Configuration

[![GitHub Release](https://img.shields.io/github/v/release/Syax89/Ariston-Cares-S-Ebusd?style=for-the-badge)](https://github.com/Syax89/Ariston-Cares-S-Ebusd/releases)
[![ebusd](https://img.shields.io/badge/ebusd-Compatible-blue?style=for-the-badge)](https://github.com/john30/ebusd)

`ebusd` configuration for **Ariston Cares S** boilers and closely related Galileo-platform models.

This repository is based on real packet captures (`dump`, `dump2`, `dump3`) and live `ebusd` validation against an `ens:192.168.4.74:9999` adapter stream.

## What is already validated

The current `aris.csv` is no longer just a guesswork file. The following areas were validated from packet dumps and confirmed again in live `ebusd` logs:

- boiler state and request status
- heating and DHW setpoints
- main temperatures and internal targets
- room/zone temperatures and zone setpoint broadcasts
- pump modulation and pressure sensor voltage

## Installation

Copy `aris.csv` and `_templates.csv` to your ebusd config directory, for example `/etc/ebusd/` or your Home Assistant add-on config path.

Example startup:

```bash
ebusd --scanconfig=0 --configpath=/etc/ebusd --device=/dev/ttyUSB0
```

For Ethernet/ENS adapters, a setup like this is also valid:

```bash
ebusd --scanconfig=0 --configpath=/config/Ariston --device=ens:192.168.4.74:9999
```

`--scanconfig=0` is recommended so `ebusd` does not fall back to generic Ariston CSV files.

If you use MQTT/Home Assistant discovery, keep `mqtt-hassio.cfg` in the same config path.

## Confirmed entities

These names are considered the most reliable right now.

| Group | Name | Meaning | Unit / Type |
| :--- | :--- | :--- | :--- |
| Status | `flame_state` | flame state from active polling | enum |
| Status | `boiler_operating_mode` | boiler operating mode | enum |
| Status | `request_status_1` | composite request/status group | status |
| Status | `request_status_2` | secondary request/status group | status |
| Heating | `heating_setpoint_triplet` | heating target triplet | degC |
| Heating | `max_heating_setpoint` | maximum heating setpoint | degC |
| Heating | `internal_flow_target_temperature` | internal flow target | degC |
| Heating | `zone1_current_setpoint` | active heating setpoint | degC |
| Heating | `zone1_current_setpoint_bc` | passive broadcast of active heating setpoint | degC |
| Water | `dhw_setpoint` | DHW setpoint | degC |
| Water | `dhw_actual_temperature` | actual DHW temperature | degC |
| Water | `temp_sanitario_eco` | ECO DHW setpoint | degC |
| Temperature | `main_flow_temperature` | main flow temperature | degC |
| Temperature | `secondary_return_temperature` | secondary return temperature | degC |
| Temperature | `aux_probe_temperature` | auxiliary probe temperature | degC |
| Temperature | `exhaust_temperature` | exhaust/flue temperature | degC |
| Temperature | `zone1_room_temperature` | room temperature | degC |
| Temperature | `outdoor_temperature_bc` | outdoor temperature broadcast | degC or invalid |
| Technical | `pump_modulation` | pump modulation value | raw numeric |
| Technical | `pressure_sensor_voltage` | pressure sensor voltage | V |
| Technical | `nominal_power_kw` | nominal boiler power | kW |

## Usable but still partly inferred

These decode consistently, but their exact physical meaning is not fully proven yet:

| Name | Current interpretation |
| :--- | :--- |
| `heating_active` | heating enable / logical heating active |
| `heating_active_bc` | passive heating state byte, not a pure boolean |
| `zone1_setpoints` | antifreeze/day/night zone setpoints |
| `zone1_request_mode_bc` | zone request mode/status |
| `zone1_heat_request_raw` | raw zone heat request byte |
| `zone1_state_triplet_bc` | zone state triplet (`heating_request`, `zone_call_state`, `zone_status_code`) |
| `heating_flame_mode` | heating-related flame mode, semantics still overlap with `flame_state` |
| `heating_flame_mode_bc` | passive heating-flame-related state |
| `current_power_level` | likely real burner power/modulation, but still worth observing |

## Important notes from validation

- `request_status_1` changes with heating mode; in the tested dumps, the `0191` subfield flips to `1` only during heating operation.
- `heating_setpoint_triplet` behaves consistently across all three dumps:
  - standby / DHW: `82.0;65.0;35.0`
  - heating active: `65.0;65.0;35.0`
- `dhw_setpoint` was confirmed live by observing writes like `41.0` and `42.0`.
- `zone1_current_setpoint_bc` tracks real setpoint changes live (`64.0`, `65.0`, `66.0`, `67.0`, etc.).
- `outdoor_temperature_bc = 3276.7` usually means raw `ff7f`, i.e. sensor absent / invalid value.
- `zone1_heat_request_raw` currently exposes the raw byte (`79` seen live) because its semantics are not fully decoded yet.

## Still unknown / experimental

The file still contains some intentionally conservative or commented-out areas:

- diagnostic blocks around `d346`, `db95`, `d994`, `dd94`
- zone schedule/curve families around `6271..6276`, `6371..6376`, `6426`
- legacy `2020`-based rows kept for observation only
- power-search test registers at the bottom of `aris.csv`

These are useful for future reverse engineering, but they are not required for day-to-day monitoring.

## Recommended MQTT entities to watch first

If you want a practical starting point in MQTT / Home Assistant, watch these first:

- `boiler_operating_mode`
- `flame_state`
- `request_status_1`
- `internal_flow_target_temperature`
- `main_flow_temperature`
- `dhw_setpoint`
- `dhw_actual_temperature`
- `zone1_current_setpoint_bc`
- `heating_setpoint_triplet`
- `current_power_level`

## Contributing

New packet captures, live logs, and validation from compatible Ariston / Chaffoteaux models are very welcome.

If you open an issue or PR, the most useful material is:

- raw `ebusd` log excerpts
- `pcapng` dumps
- a short note describing what changed physically on the boiler (DHW setpoint, heating setpoint, burner start/stop, etc.)

## License

MIT License.
