# StromGedacht for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/V4n1X/ha_stromgedacht)](https://github.com/V4n1X/ha_stromgedacht/releases)
[![Maintainer](https://img.shields.io/badge/maintainer-V4n1X-blue)](https://github.com/V4n1X)

> [🇩🇪 Deutsche Anleitung / German Description](README_de.md)

This custom integration integrates the [StromGedacht API](https://api.stromgedacht.de) (provided by TransnetBW) into Home Assistant. It provides information about the current state of the power grid in Baden-Württemberg (Germany), including warnings to reduce consumption or signals to use energy (super green state).

## ✨ Features

* **Easy Configuration:** Setup via Home Assistant UI.
* **Mandatory Zip Code:** Get localized data for your area.
* **Real-time Data:** Fetches grid status (Green/Yellow/Red/SuperGreen).
* **Forecast Data:** Provides sensors for **Grid Load**, **Renewable Energy**, and **Residual Load** (in MW).
* **Short Status Mode:** Choose between a detailed status text or a short version (Red, Orange, Green, Supergreen).
* **Configurable Interval:** Adjust the update frequency via integration options.

## 🖼️ Preview

<p align="left">
  <img src="https://github.com/user-attachments/assets/f12b0c5e-2115-40ba-b548-47548c1bc120" alt="StromGedacht Dashboard Example" width="600">
</p>

## 📥 Installation

### Option 1: HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=V4n1X&repository=ha_stromgedacht&category=Integration)

1.  Open HACS in Home Assistant.
2.  Go to **Integrations** > Top right menu (3 dots) > **Custom repositories**.
3.  Add the URL: `https://github.com/V4n1X/ha_stromgedacht`
4.  Category: **Integration**.
5.  Click **Add**.
6.  Search for **StromGedacht** in HACS and install it.
7.  Restart Home Assistant.

### Option 2: Manual

1.  Download the latest release.
2.  Copy the folder `stromgedacht` (inside `custom_components`) to your Home Assistant `config/custom_components/` directory.
3.  Restart Home Assistant.

## ⚙️ Configuration

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration**.
3.  Search for **StromGedacht**.
4.  Enter your **Zip Code (PLZ)** (e.g., `70173`).
5.  (Optional) Set the scan interval.

## 📊 Entities & States

### Sensors
The integration creates the following sensors:
* **Status:** The traffic light system (text).
* **Load:** Current grid load in MW.
* **Renewable Energy:** Current generation from renewables in MW.
* **Residual Load:** The difference between load and renewables in MW.

### State Meanings
The main status sensor follows the official StromGedacht logic:

| Value | State | Meaning |
| :--- | :--- | :--- |
| **-1** | **Super Green** | 🍃 Power is abundant. Use electricity now to support the grid! |
| **1** | **Green** | ✅ Normal operation. No action required. |
| **3** | **Orange** | ⚠️ Reduce consumption to save costs and CO2. |
| **4** | **Red** | ⚡ Reduce consumption immediately to prevent power shortages. |

---

**Disclaimer:** This is a private project and not an official product of TransnetBW GmbH.
