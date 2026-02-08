# Ariston Cares S ebusd Configuration 🛡️🔥

[![GitHub Release](https://img.shields.io/github/v/release/Syax89/Ariston-Cares-S-Ebusd?style=for-the-badge)](https://github.com/Syax89/Ariston-Cares-S-Ebusd/releases)
[![ebusd](https://img.shields.io/badge/ebusd-Compatible-blue?style=for-the-badge)](https://github.com/john30/ebusd)

Highly optimized and tested `ebusd` configuration for **Ariston Cares S** boilers (and compatible models like **Chaffoteaux Inoa S**).

## 🌟 Why this configuration?

Generic Ariston CSV files often fail with entry-level boilers (Galileo platform). This configuration solves:
*   **KW Power Fix**: Corrected power calculation using divisor 2560 (no more 1400kW readings).
*   **Real-time DHW**: Captures Domestic Hot Water setpoint changes via passive broadcast (since polling is blocked by firmware).
*   **Ghost Sensor Removal**: Disabled external probes and pressure sensors not physically present on Cares S to prevent log errors.
*   **Flame Status Fix**: Correctly interprets status `3` as Post-circulation (OFF).

---

## 🛠️ Hardware Requirements

1.  **ebus Adapter**: [ebusd adapter v3 or v5](https://adapter.ebusd.eu/) is highly recommended.
2.  **Connection**: Connect the adapter to the `eBUS` port on the boiler mainboard.
3.  **Software**: A running instance of `ebusd`.

## ⚙️ Installation & Usage

### 1. Download
Download `aris.csv` and `_templates.csv` to your ebusd configuration directory (e.g., `/etc/ebusd/`).

### 2. Configure ebusd
Add the following parameter to your ebusd startup config to force-load this file:
```bash
ebusd --scanconfig=0 --configpath=/etc/ebusd --device=/dev/ttyUSB0
```
*Note: Using `--scanconfig=0` prevents ebusd from loading generic, buggy files.*

### 3. MQTT Integration (Home Assistant)
If using the Home Assistant MQTT Discovery, ensure `mqtt-hassio.cfg` is present in your config path.

---

## 📊 Mapped Entities

| Category | Sensor | Description |
| :--- | :--- | :--- |
| **Status** | `stato_fiamma` | On/Off state of the burner |
| **Status** | `caldaia_mode` | Operating mode (Stand-by, Heating, DHW) |
| **Technical** | `power_level` | Real-time modulation power in **kW** |
| **Technical** | `modulazione_pompa` | Pump duty cycle (0-255) |
| **Heating** | `temp_flow_main` | Main flow temperature |
| **Water** | `temp_sanitario` | Real DHW output temperature |

---

## 🤝 Contributing
Contributions, tests on different Ariston models, and log captures are welcome! Open an Issue or PR.

## ⚖️ License
MIT License. Free to use and modify.

---
*Disclaimer: Use at your own risk. Incorrect eBUS commands can theoretically alter boiler parameters.*
