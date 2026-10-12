# StromGedacht for Home Assistant

[![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/V4n1X/ha_stromgedacht)](https://github.com/V4n1X/ha_stromgedacht/releases)
[![Tests](https://github.com/V4n1X/ha_stromgedacht/actions/workflows/tests.yaml/badge.svg)](https://github.com/V4n1X/ha_stromgedacht/actions/workflows/tests.yaml)
[![Maintainer](https://img.shields.io/badge/maintainer-V4n1X-blue)](https://github.com/V4n1X)

> [🇩🇪 Deutsche Anleitung / German Description](README_de.md)

This custom integration integrates the [StromGedacht API](https://api.stromgedacht.de) (provided by TransnetBW) into Home Assistant. It provides information about the current state of the power grid in Baden-Württemberg (Germany), including warnings to reduce consumption or signals to use energy (super green state).

## ✨ Features

* **Easy Configuration:** Setup via the Home Assistant UI.
* **Zip Code Based:** Get localized data for your area.
* **Real-time Status:** Grid traffic light (Super Green / Green / Orange / Red).
* **Forecast Data:** Sensors for **Grid Load**, **Renewable Energy** and **Residual Load** (in MW), including the forecast series for charts.
* **Automation Triggers:** Device triggers like *"Grid status becomes Super Green"*, e.g. to start power-hungry devices when there is a surplus of power.
* **Short Status Mode:** Choose between a detailed status text or a short version (Red, Orange, Green, Super Green).
* **Configurable Interval:** Adjust the update frequency via the integration options.

## 🖼️ Preview

<p align="left">
  <img src="https://github.com/user-attachments/assets/f12b0c5e-2115-40ba-b548-47548c1bc120" alt="StromGedacht Dashboard Example" width="600">
</p>

## 📦 Installation

Requires Home Assistant **2025.8** or newer.

### Option 1: HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=V4n1X&repository=ha_stromgedacht&category=Integration)

1.  Open HACS in Home Assistant.
2.  Search for **StromGedacht** and install it.
3.  Restart Home Assistant.

### Option 2: Manual

1.  Download the latest release.
2.  Copy the folder `stromgedacht` (inside `custom_components`) to your Home Assistant `config/custom_components/` directory.
3.  Restart Home Assistant.

## ⚙️ Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=stromgedacht)

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for **StromGedacht**.
3.  Enter your **Zip Code (PLZ)** (e.g. `70173`).
4.  (Optional) Set the update interval and the short status mode.

Only zip codes in the TransnetBW grid area (mostly Baden-Württemberg) are supported by StromGedacht. The update interval and the status mode can be changed later via **Configure** on the integration.

## 📊 Entities & States

### Sensors

| Sensor | Description | Attributes |
| :--- | :--- | :--- |
| **Status** | The grid traffic light | `description`, `future_states` (upcoming states of the next 24 h), `zip_code` |
| **Grid Load** | Current grid load in MW | `data_series` (forecast series) |
| **Renewable Energy** | Current generation from renewables in MW | `data_series` (forecast series) |
| **Residual Load** | Difference between load and renewables in MW | `data_series` (forecast series) |

The large attributes `future_states` and `data_series` are not stored in the recorder database to keep it small.

### State Meanings

The status sensor follows the official StromGedacht logic:

| API Value | State | Meaning |
| :--- | :--- | :--- |
| **-1** | `super_green` | 🌱 Power is abundant. Use electricity now to support the grid! |
| **1** | `green` | ✅ Normal operation. No action required. |
| **3** | `orange` | 🟠 Reduce consumption to save costs and CO2. |
| **4** | `red` | 🔴 Reduce consumption immediately to prevent power shortages. |

## 🤖 Automations

In the automation editor, choose **Device** as trigger, select your StromGedacht device and pick one of the triggers, e.g. **Grid status becomes Super Green**. An optional duration can be set.

Alternatively, use a state trigger in YAML:

```yaml
automation:
  - alias: "Start heat pump boost on super green"
    triggers:
      - trigger: state
        entity_id: sensor.stromgedacht_70173_status
        to: "super_green"
    actions:
      - action: switch.turn_on
        target:
          entity_id: switch.heat_pump_boost
```

## 📈 Forecast Chart

The `data_series` attribute can be used to show the forecast, e.g. with the [ApexCharts Card](https://github.com/RomRider/apexcharts-card):

```yaml
type: custom:apexcharts-card
graph_span: 2d
span:
  start: hour
  offset: -2h
series:
  - entity: sensor.stromgedacht_70173_residual_load
    name: Residual Load
    data_generator: |
      return entity.attributes.data_series.map((entry) => {
        return [new Date(entry.dateTime).getTime(), entry.value];
      });
```

## 🛠️ Development

The tests run against the Home Assistant version pinned in `requirements_test.txt` (Linux or WSL, Home Assistant does not run on Windows):

```bash
pip install -r requirements_test.txt
python -m pytest
```

---

**Disclaimer:** This is a private project and not an official product of TransnetBW GmbH.
