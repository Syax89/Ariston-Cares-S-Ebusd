# ebusd Configuration for Ariston Cares S (and compatible)

This repository provides a highly optimized and tested `ebusd` configuration CSV file for **Ariston Cares S** boilers (also valid for similar entry-level models like **Chaffoteaux Inoa S**).

Unlike generic configurations, this file is tuned to solve common issues with "entry-level" Ariston boilers, such as fake sensor readings, missing pressure transducers, and "silent" DHW (Domestic Hot Water) setpoints.

## 🚀 Features

* **✅ Zero Errors:** Filtered out unsupported polling commands that cause "ERR: sent/read timeout" in logs.
* **🔥 Real-time DHW Setpoint:** Captures the knob change instantly via Broadcast decoding (since polling is not supported).
* **⚡ Correct Power Reading:** Fixed the kW calculation (using divisor 2560 instead of 10) to show real power (e.g., 5.5 kW instead of 1400 kW).
* **🛠️ Hardware Specifics:**
    * Disabled Digital Pressure Sensor (Cares S uses a simple ON/OFF switch).
    * Disabled External Probe (prevents `3276.7 °C` error value).
    * Corrected Flame Status (interprets status `3` as OFF/Post-circulation, not ON).
* **🇮🇹 Italian Labels:** All sensors are named clearly in Italian (easily translatable).

## 📋 Prerequisities

* **Hardware:** An eBUS adapter (e.g., ebusd adapter v3/v5).
* **Software:** [ebusd](https://github.com/john30/ebusd) installed (via Docker, HA Add-on, or native).
* **Boiler:** Ariston Cares S, Chaffoteaux Inoa S, or similar "Galileo" platform entry-level boilers.

## ⚙️ Installation

1.  Download the `aris.csv` file from this repository.
2.  Place it in your ebusd configuration folder (usually `/etc/ebusd/` or `/config/ebusd/`).
3.  Configure your ebusd launch parameters to load this file. Example:
    ```bash
    ebusd --scanconfig=0 --configpath=/etc/ebusd --device=...
    ```
    *(Note: `--scanconfig=0` is recommended to force using this specific file if auto-discovery fails or loads a generic buggy file).*

## 📊 Key Sensors Mapped

| Sensor Name (CSV) | Description | Notes |
| :--- | :--- | :--- |
| `stato_fiamma` | Flame Status | Correctly handles "3" as Post-circulation (OFF) |
| `temp_sanitario` | DHW Output Temp | Broadcast (passive) reading |
| `set_sanitario` | DHW Setpoint | **Broadcast only** (Polling not supported on this model) |
| `livello_potenza` | Current Power (kW) | Precision fix (Divisor 2560) |
| `modulazione_pompa`| Pump Duty Cycle | Raw value 0-255 (convert to % in HA) |
| `caldaia_mode` | Operation Mode | Stand-by, Winter, Summer, Error codes |

## 🏠 Home Assistant Integration (MQTT)

This configuration works natively with Home Assistant via MQTT Discovery.

**Tip for Pump Modulation:**
The boiler sends raw 0-255 values. To see percentage in HA, add this to your `configuration.yaml`:

```yaml
mqtt:
  sensor:
    - name: "Modulazione Pompa"
      state_topic: "ebusd/aris/modulazione_pompa"
      unit_of_measurement: "%"
      value_template: "{{ (value_json['val'].value | float(0) / 2.55) | round(0) }}"
