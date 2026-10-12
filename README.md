<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="images/stromgedacht_logo_dark.svg">
    <img src="images/stromgedacht_logo.svg" alt="StromGedacht" width="420">
  </picture>
</p>

<h1 align="center">StromGedacht for Home Assistant</h1>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Default-41BDF5.svg" alt="HACS Default"></a>
  <a href="https://github.com/V4n1X/ha_stromgedacht/releases"><img src="https://img.shields.io/github/v/release/V4n1X/ha_stromgedacht" alt="GitHub release"></a>
  <a href="https://github.com/V4n1X/ha_stromgedacht/actions/workflows/tests.yaml"><img src="https://github.com/V4n1X/ha_stromgedacht/actions/workflows/tests.yaml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/V4n1X"><img src="https://img.shields.io/badge/maintainer-V4n1X-blue" alt="Maintainer"></a>
</p>

<p align="center">
  <a href="README_de.md">🇩🇪 Deutsche Anleitung</a>
</p>

This custom integration brings [StromGedacht](https://www.stromgedacht.de), the grid traffic light of the transmission system operator TransnetBW, into Home Assistant. It shows the current and upcoming state of the power grid in Baden-Württemberg (Germany) and helps you to **shift your consumption** to times with a lot of renewable energy and away from times when the grid is under pressure.

## 📑 Contents

- [Features](#-features)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Entities](#-entities)
- [Planning your consumption](#-planning-your-consumption)
- [Automations](#-automations)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)

## ✨ Features

- **Grid traffic light:** Current state of the grid (Super Green / Green / Orange / Red) for your zip code.
- **Look ahead:** Upcoming states of the next 48 hours, plus the start of the **next super green** and the **next reduce consumption** period.
- **Best time to consume:** The time with the lowest residual load (highest share of renewables) in the forecast.
- **Forecast data:** Grid load, renewable energy, residual load and the super green threshold in MW, including the forecast series for charts.
- **Automation triggers:** Device triggers like *"Grid status becomes Super Green"* and timestamp sensors usable as time triggers.
- **Setup via UI:** No YAML needed, German and English translations.

## 📸 Preview

<p align="left">
  <img src="https://github.com/user-attachments/assets/f12b0c5e-2115-40ba-b548-47548c1bc120" alt="StromGedacht Dashboard Example" width="600">
</p>

## 📦 Installation

Requires Home Assistant **2025.8** or newer.

### 🚀 HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=V4n1X&repository=ha_stromgedacht&category=Integration)

1. Open HACS in Home Assistant.
2. Search for **StromGedacht** and install it.
3. Restart Home Assistant.

### 🔨 Manual

1. Download the latest [release](https://github.com/V4n1X/ha_stromgedacht/releases).
2. Copy the folder `custom_components/stromgedacht` to the `config/custom_components/` directory of your Home Assistant.
3. Restart Home Assistant.

## 🔧 Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=stromgedacht)

1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **StromGedacht**.
3. Enter your zip code and adjust the options if needed.

| Option | Description | Default |
| :--- | :--- | :--- |
| **Zip Code** | German zip code (5 digits) within the TransnetBW grid area | – |
| **Update Interval** | How often the data is fetched, in minutes (minimum 5) | `15` |
| **Short status text** | Show only the color (e.g. "Green") instead of the full description | off |

The update interval and the short status text can be changed later via **Configure** on the integration. To monitor several zip codes, add the integration once per zip code.

## 📊 Entities

All entities belong to one device per zip code.

> [!NOTE]
> The entity IDs depend on the language of your Home Assistant. The examples in this README use English entity IDs with the zip code `70173`, e.g. `sensor.stromgedacht_70173_residual_load`. In German it is `sensor.stromgedacht_70173_residuallast`. You find your entity IDs on the device page of the integration.

### 🚦 Status

| Entity | Description | Attributes |
| :--- | :--- | :--- |
| `sensor.stromgedacht_70173_status` | The grid traffic light | `description`, `future_states` (upcoming states of the next 48 h), `zip_code` |

| API value | State | Meaning |
| :--- | :--- | :--- |
| -1 | `super_green` | 🌱 Power is abundant. Use electricity now to support the grid! |
| 1 | `green` | ✅ Normal operation. No action required. |
| 3 | `orange` | 🟠 Reduce consumption to save costs and CO2. |
| 4 | `red` | 🔴 Reduce consumption immediately to prevent power shortages. |

The short status text option only changes the displayed text. Automations always use the states from the table.

### 📅 Planning

| Entity | Description | Attributes |
| :--- | :--- | :--- |
| `sensor.stromgedacht_70173_best_consumption_time` | Start of the 15 minute slot with the lowest residual load until the end of the forecast | `residual_load`, `forecast_until` |
| `sensor.stromgedacht_70173_next_super_green` | Start of the current or next super green period | `end`, `state` |
| `sensor.stromgedacht_70173_next_reduce_consumption` | Start of the current or next orange or red period | `end`, `state` (`orange` or `red`) |

These are timestamp sensors. They are `unknown` if there is no such period or forecast ahead. If a period is already running, the sensor shows its start in the past and the `end` attribute tells you how long it lasts.

### ⚡ Forecast

| Entity | Description | Attributes |
| :--- | :--- | :--- |
| `sensor.stromgedacht_70173_grid_load` | Current grid load in MW | `data_series` |
| `sensor.stromgedacht_70173_renewable_energy` | Current generation from renewables in MW | `data_series` |
| `sensor.stromgedacht_70173_residual_load` | Grid load minus renewable generation in MW | `data_series` |
| `sensor.stromgedacht_70173_super_green_threshold` | StromGedacht threshold for the super green state in MW | `data_series` |

`data_series` contains the 15 minute values from two hours ago until the end of the forecast (usually the end of the next day), each as `{"dateTime": ..., "value": ...}`. The attributes `future_states` and `data_series` are not stored in the recorder database to keep it small.

## 🔮 Planning your consumption

The traffic light tells you what to do *now*. To decide *when* to run flexible consumers like the dishwasher, washing machine, EV charging or a heat pump boost, look at the **residual load**: the part of the consumption that is not covered by renewable energy. The lower it is, the greener your electricity. Unlike a nationwide EPEX price chart, these values are specific to the TransnetBW grid area.

- **Best Consumption Time** directly tells you the best slot in the forecast.
- **Next Super Green** and **Next Reduce Consumption** tell you when the next periods start and end.
- The forecast sensors provide the complete curves for charts.

### 📈 Forecast chart

With the [ApexCharts Card](https://github.com/RomRider/apexcharts-card) (available in HACS) you get a forecast chart similar to the StromGedacht app:

<details>
<summary>Card configuration</summary>

```yaml
type: custom:apexcharts-card
graph_span: 32h
span:
  start: hour
  offset: -2h
header:
  show: true
  title: StromGedacht Forecast (MW)
  show_states: true
  colorize_states: true
now:
  show: true
  label: Now
  color: "#e74c3c"
yaxis:
  - id: power
    decimals: 0
series:
  - entity: sensor.stromgedacht_70173_grid_load
    name: Grid Load
    yaxis_id: power
    color: "#1f77b4"
    stroke_width: 3
    data_generator: |
      return entity.attributes.data_series.map((e) => [new Date(e.dateTime).getTime(), e.value]);
  - entity: sensor.stromgedacht_70173_renewable_energy
    name: Renewable Energy
    yaxis_id: power
    type: area
    color: "#2ca02c"
    opacity: 0.15
    stroke_width: 2
    data_generator: |
      return entity.attributes.data_series.map((e) => [new Date(e.dateTime).getTime(), e.value]);
  - entity: sensor.stromgedacht_70173_residual_load
    name: Residual Load
    yaxis_id: power
    color: "#ff7f0e"
    stroke_width: 2
    data_generator: |
      return entity.attributes.data_series.map((e) => [new Date(e.dateTime).getTime(), e.value]);
  - entity: sensor.stromgedacht_70173_super_green_threshold
    name: Super Green Threshold
    yaxis_id: power
    color: "#00c853"
    stroke_width: 2
    stroke_dash: 4
    show:
      in_header: false
    data_generator: |
      return entity.attributes.data_series.map((e) => [new Date(e.dateTime).getTime(), e.value]);
```

</details>

### 📋 Upcoming states

A markdown card lists the upcoming traffic light states and the best time:

<details>
<summary>Card configuration</summary>

```yaml
type: markdown
title: StromGedacht
content: |
  {%- set names = {"super_green": "🌱 Super Green", "green": "✅ Green", "orange": "🟠 Orange", "red": "🔴 Red"} %}
  {%- set codes = {-1: "super_green", 1: "green", 3: "orange", 4: "red"} %}
  {%- for s in state_attr("sensor.stromgedacht_70173_status", "future_states") or [] %}
  - {{ as_timestamp(s.from) | timestamp_custom("%a %H:%M") }} – {{ as_timestamp(s.to) | timestamp_custom("%a %H:%M") }}: {{ names[codes[s.state]] }}
  {%- endfor %}

  **Best time:** {{ as_timestamp(states("sensor.stromgedacht_70173_best_consumption_time"), 0) | timestamp_custom("%a %H:%M") }}
```

</details>

## 🤖 Automations

### 🎯 Device triggers

In the automation editor, choose **Device** as trigger, select your StromGedacht device and pick one of the triggers, e.g. **Grid status becomes Super Green**. An optional duration can be set.

### 💡 Examples

<details>
<summary>Turn on a consumer when the grid gets super green</summary>

```yaml
triggers:
  - trigger: state
    entity_id: sensor.stromgedacht_70173_status
    to: "super_green"
actions:
  - action: switch.turn_on
    target:
      entity_id: switch.heat_pump_boost
```

</details>

<details>
<summary>Start the dishwasher at the best time</summary>

The best time is updated with every forecast update, so the automation always uses the latest forecast.

```yaml
triggers:
  - trigger: time
    at: sensor.stromgedacht_70173_best_consumption_time
conditions:
  - condition: state
    entity_id: input_boolean.dishwasher_ready
    state: "on"
actions:
  - action: switch.turn_on
    target:
      entity_id: switch.dishwasher
```

</details>

<details>
<summary>Get a warning one hour before consumption should be reduced</summary>

```yaml
triggers:
  - trigger: time
    at:
      entity_id: sensor.stromgedacht_70173_next_reduce_consumption
      offset: "-01:00:00"
actions:
  - action: notify.notify
    data:
      message: >
        StromGedacht: reduce consumption from
        {{ as_timestamp(states("sensor.stromgedacht_70173_next_reduce_consumption")) | timestamp_custom("%H:%M") }}
        until {{ as_timestamp(state_attr("sensor.stromgedacht_70173_next_reduce_consumption", "end")) | timestamp_custom("%H:%M") }}.
```

</details>

## ❓ Troubleshooting

**"StromGedacht provides no data for this zip code"**
StromGedacht only covers the grid area of TransnetBW, which is mostly Baden-Württemberg.

**The examples don't work with my entities**
Check the entity IDs on the device page of the integration, they depend on the language of your Home Assistant (see [Entities](#-entities)).

**A planning sensor shows a time in the past**
The period is already running, the `end` attribute shows when it ends. The planning sensors are recalculated with every update, so after a period has ended it can take up to one update interval until the next one is shown.

**All sensors are unavailable**
The StromGedacht API could not be reached. The integration retries automatically with the next update. Details are in the Home Assistant log.

## 🧪 Development

The tests run against the Home Assistant version pinned in `requirements_test.txt` (Linux or WSL, Home Assistant does not run on Windows):

```bash
pip install -r requirements_test.txt
python -m pytest
```

Issues and pull requests are welcome.

## 📄 License & Disclaimer

This project is licensed under the [MIT License](LICENSE).

This is a private project and not an official product of TransnetBW GmbH. Data provided by the [StromGedacht API](https://api.stromgedacht.de). The StromGedacht name and logo belong to TransnetBW GmbH.
