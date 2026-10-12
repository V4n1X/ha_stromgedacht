# StromGedacht für Home Assistant

[![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/V4n1X/ha_stromgedacht)](https://github.com/V4n1X/ha_stromgedacht/releases)
[![Tests](https://github.com/V4n1X/ha_stromgedacht/actions/workflows/tests.yaml/badge.svg)](https://github.com/V4n1X/ha_stromgedacht/actions/workflows/tests.yaml)

> [🇬🇧 English Description](README.md)

Diese Custom Integration bindet die [StromGedacht API](https://api.stromgedacht.de) (von TransnetBW) in Home Assistant ein. Sie liefert Informationen über den aktuellen Status des Stromnetzes in Baden-Württemberg, einschließlich Warnungen zur Verbrauchsreduzierung oder Hinweisen zur Nutzung von Überschussstrom.

## ✨ Funktionen

* **Einfache Einrichtung:** Konfiguration komplett über die Benutzeroberfläche (UI).
* **PLZ-basiert:** Lokalisierte Daten für deinen Standort.
* **Echtzeit-Status:** Ampelsystem (Supergrün / Grün / Orange / Rot).
* **Leistungsdaten:** Sensoren für **Netzlast**, **Erneuerbare Energie** und **Residuallast** (in MW), inklusive Prognoseverlauf für Diagramme.
* **Automationen:** Geräte-Auslöser wie *„Netzstatus wird Supergrün“*, z.B. um stromhungrige Geräte bei Stromüberschuss einzuschalten.
* **Kurzer Statustext:** Wähle zwischen dem vollen Text oder einer kurzen Version (Rot, Orange, Grün, Supergrün).
* **Anpassbar:** Das Aktualisierungsintervall kann in den Optionen geändert werden.

## 🖼️ Vorschau

<p align="left">
  <img src="https://github.com/user-attachments/assets/f12b0c5e-2115-40ba-b548-47548c1bc120" alt="StromGedacht Dashboard Example" width="600">
</p>

## 📦 Installation

Voraussetzung ist Home Assistant **2025.8** oder neuer.

### Option 1: HACS (Empfohlen)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=V4n1X&repository=ha_stromgedacht&category=Integration)

1.  Öffne HACS in Home Assistant.
2.  Suche nach **StromGedacht** und installiere es.
3.  Starte Home Assistant neu.

### Option 2: Manuell

1.  Lade das neueste Release herunter.
2.  Kopiere den Ordner `stromgedacht` (aus `custom_components`) in dein Home Assistant Verzeichnis: `config/custom_components/`.
3.  Starte Home Assistant neu.

## ⚙️ Konfiguration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=stromgedacht)

1.  Gehe zu **Einstellungen** > **Geräte & Dienste**.
2.  Klicke auf **Integration hinzufügen** und suche nach **StromGedacht**.
3.  Gib deine **Postleitzahl** ein (z.B. `70173`).
4.  (Optional) Passe das Abrufintervall und den kurzen Statustext an.

StromGedacht unterstützt nur Postleitzahlen im Netzgebiet der TransnetBW (überwiegend Baden-Württemberg). Abrufintervall und Statustext lassen sich später über **Konfigurieren** an der Integration ändern.

## 📊 Entitäten & Status

### Sensoren

| Sensor | Beschreibung | Attribute |
| :--- | :--- | :--- |
| **Status** | Das Ampelsystem | `description`, `future_states` (kommende Zustände der nächsten 24 h), `zip_code` |
| **Netzlast** | Aktueller Stromverbrauch im Netz (MW) | `data_series` (Prognoseverlauf) |
| **Erneuerbare Energie** | Aktuelle Erzeugung aus Wind/Sonne (MW) | `data_series` (Prognoseverlauf) |
| **Residuallast** | Differenz aus Last und Erneuerbaren (MW) | `data_series` (Prognoseverlauf) |

Die großen Attribute `future_states` und `data_series` werden nicht in der Recorder-Datenbank gespeichert, damit diese klein bleibt.

### Bedeutung der Zustände

Der Status-Sensor folgt der offiziellen Logik der StromGedacht-App:

| API-Wert | Zustand | Bedeutung |
| :--- | :--- | :--- |
| **-1** | `super_green` | 🌱 Strom jetzt nutzen, um die Netzdienlichkeit zu unterstützen. |
| **1** | `green` | ✅ Normalbetrieb - Du musst nichts weiter tun. |
| **3** | `orange` | 🟠 Verbrauch reduzieren, um Kosten und CO2 zu sparen. |
| **4** | `red` | 🔴 Verbrauch reduzieren, um Strommangel zu verhindern. |

## 🤖 Automationen

Wähle im Automationseditor **Gerät** als Auslöser, dann dein StromGedacht-Gerät und einen der Auslöser, z.B. **Netzstatus wird Supergrün**. Optional kann eine Dauer angegeben werden.

Alternativ als Zustands-Auslöser in YAML:

```yaml
automation:
  - alias: "Wärmepumpe bei Supergrün hochfahren"
    triggers:
      - trigger: state
        entity_id: sensor.stromgedacht_70173_status
        to: "super_green"
    actions:
      - action: switch.turn_on
        target:
          entity_id: switch.waermepumpe_boost
```

## 📈 Prognose-Diagramm

Das Attribut `data_series` kann für Prognose-Diagramme genutzt werden, z.B. mit der [ApexCharts Card](https://github.com/RomRider/apexcharts-card):

```yaml
type: custom:apexcharts-card
graph_span: 2d
span:
  start: hour
  offset: -2h
series:
  - entity: sensor.stromgedacht_70173_residual_load
    name: Residuallast
    data_generator: |
      return entity.attributes.data_series.map((entry) => {
        return [new Date(entry.dateTime).getTime(), entry.value];
      });
```

---

**Hinweis:** Dies ist ein privates Projekt und kein offizielles Produkt der TransnetBW GmbH.
