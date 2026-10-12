# StromGedacht für Home Assistant

[![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/V4n1X/ha_stromgedacht)](https://github.com/V4n1X/ha_stromgedacht/releases)
[![Tests](https://github.com/V4n1X/ha_stromgedacht/actions/workflows/tests.yaml/badge.svg)](https://github.com/V4n1X/ha_stromgedacht/actions/workflows/tests.yaml)
[![Maintainer](https://img.shields.io/badge/maintainer-V4n1X-blue)](https://github.com/V4n1X)

> [🇬🇧 English Description](README.md)

Diese Custom Integration bringt den Dienst [StromGedacht](https://www.stromgedacht.de) des Übertragungsnetzbetreibers TransnetBW in Home Assistant. Sie zeigt den aktuellen und kommenden Zustand des Stromnetzes in Baden-Württemberg und hilft dir, deinen **Verbrauch zu verschieben** – hin zu Zeiten mit viel erneuerbarer Energie und weg von Zeiten, in denen das Netz unter Druck steht.

## Inhalt

- [Funktionen](#-funktionen)
- [Installation](#-installation)
- [Konfiguration](#️-konfiguration)
- [Entitäten](#-entitäten)
- [Verbrauch planen](#-verbrauch-planen)
- [Automationen](#-automationen)

## ✨ Funktionen

* **Netz-Ampel:** Aktueller Zustand des Stromnetzes (Supergrün / Grün / Orange / Rot) für deine Postleitzahl.
* **Vorschau:** Kommende Zustände der nächsten 48 Stunden sowie Sensoren für den Beginn des **nächsten Supergrün**- und des **nächsten Verbrauchsreduzierungs**-Zeitraums.
* **Beste Verbrauchszeit:** Der Zeitpunkt mit der niedrigsten Residuallast (höchster Anteil Erneuerbarer) in der Prognose.
* **Prognosedaten:** Netzlast, Erneuerbare Energie, Residuallast und Supergrün-Schwelle in MW, inklusive Prognoseverlauf für Diagramme.
* **Automationen:** Geräte-Auslöser wie *„Netzstatus wird Supergrün“*, Zeitstempel-Sensoren als Zeit-Auslöser nutzbar.
* **Einrichtung per UI:** Postleitzahl, Abrufintervall und kurzer Statustext.

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

StromGedacht unterstützt nur Postleitzahlen im Netzgebiet der TransnetBW (überwiegend Baden-Württemberg). Mehrere Postleitzahlen können als eigene Einträge hinzugefügt werden. Abrufintervall (Standard 15 Minuten, mindestens 5) und Statustext lassen sich später über **Konfigurieren** an der Integration ändern.

## 📊 Entitäten

Alle Entitäten gehören zu einem Gerät pro Postleitzahl. Die Entitäts-IDs hängen von der Sprache deiner Home-Assistant-Installation ab. Die Beispiele unten verwenden deutsche IDs, z.B. `sensor.stromgedacht_70173_residuallast` (Englisch: `sensor.stromgedacht_70173_residual_load`).

### Status

| Sensor | Beschreibung | Attribute |
| :--- | :--- | :--- |
| **Status** | Die Netz-Ampel | `description`, `future_states` (kommende Zustände der nächsten 48 h), `zip_code` |

Der Status-Sensor folgt der offiziellen Logik von StromGedacht:

| API-Wert | Zustand | Bedeutung |
| :--- | :--- | :--- |
| **-1** | `super_green` | 🌱 Strom jetzt nutzen, um die Netzdienlichkeit zu unterstützen. |
| **1** | `green` | ✅ Normalbetrieb - Du musst nichts weiter tun. |
| **3** | `orange` | 🟠 Verbrauch reduzieren, um Kosten und CO2 zu sparen. |
| **4** | `red` | 🔴 Verbrauch reduzieren, um Strommangel zu verhindern. |

Mit der Option **Kurzer Statustext** wird nur die Farbe angezeigt (z.B. „Grün“). In Automationen gelten immer die Zustände aus der Tabelle.

### Planung

| Sensor | Beschreibung | Attribute |
| :--- | :--- | :--- |
| **Nächstes Supergrün** | Beginn des aktuellen oder nächsten Supergrün-Zeitraums | `end`, `state` |
| **Nächste Verbrauchsreduzierung** | Beginn des aktuellen oder nächsten orangen oder roten Zeitraums | `end`, `state` (`orange` oder `red`) |
| **Beste Verbrauchszeit** | Beginn des 15-Minuten-Abschnitts mit der niedrigsten Residuallast von jetzt bis zum Ende der Prognose | `residual_load`, `forecast_until` |

Das sind Zeitstempel-Sensoren. Sie sind `unknown`, wenn kein solcher Zeitraum bzw. keine Prognose vorliegt. Läuft ein Zeitraum bereits, zeigt der Sensor dessen Beginn in der Vergangenheit, und `end` verrät, wie lange er noch dauert.

### Prognose

| Sensor | Beschreibung | Attribute |
| :--- | :--- | :--- |
| **Netzlast** | Aktuelle Netzlast in MW | `data_series` |
| **Erneuerbare Energie** | Aktuelle Erzeugung aus Erneuerbaren in MW | `data_series` |
| **Residuallast** | Netzlast abzüglich erneuerbarer Erzeugung in MW | `data_series` |
| **Supergrün-Schwelle** | Schwelle von StromGedacht für den Zustand Supergrün in MW | `data_series` |

`data_series` enthält die 15-Minuten-Werte von vor zwei Stunden bis zum Ende der Prognose (meist Ende des Folgetags), jeweils als `{"dateTime": ..., "value": ...}`.

Die großen Attribute `future_states` und `data_series` werden nicht in der Recorder-Datenbank gespeichert, damit diese klein bleibt.

## 🔮 Verbrauch planen

Die Ampel sagt dir, was du *jetzt* tun solltest. Um zu entscheiden, *wann* flexible Verbraucher wie Spülmaschine, Waschmaschine, E-Auto oder Wärmepumpe laufen sollen, hilft die **Residuallast**: Sie ist der Teil des Verbrauchs, der nicht durch erneuerbare Energie gedeckt ist. Je niedriger sie ist, desto grüner ist dein Strom. Anders als ein bundesweiter EPEX-Preischart gelten diese Werte speziell für das Netzgebiet der TransnetBW.

* **Beste Verbrauchszeit** nennt dir direkt den besten Zeitpunkt in der Prognose.
* **Nächstes Supergrün** und **Nächste Verbrauchsreduzierung** zeigen, wann die nächsten Zeiträume beginnen und enden.
* Die Prognose-Sensoren liefern die kompletten Verläufe für Diagramme.

### Prognose-Diagramm

Mit der [ApexCharts Card](https://github.com/RomRider/apexcharts-card) (über HACS installierbar) erhältst du ein Prognose-Diagramm ähnlich der StromGedacht-App:

```yaml
type: custom:apexcharts-card
graph_span: 32h
span:
  start: hour
  offset: -2h
header:
  show: true
  title: StromGedacht Prognose (MW)
  show_states: true
  colorize_states: true
now:
  show: true
  label: Jetzt
  color: "#e74c3c"
yaxis:
  - id: power
    decimals: 0
series:
  - entity: sensor.stromgedacht_70173_netzlast
    name: Netzlast
    yaxis_id: power
    color: "#1f77b4"
    stroke_width: 3
    data_generator: |
      return entity.attributes.data_series.map((e) => [new Date(e.dateTime).getTime(), e.value]);
  - entity: sensor.stromgedacht_70173_erneuerbare_energie
    name: Erneuerbare Energie
    yaxis_id: power
    type: area
    color: "#2ca02c"
    opacity: 0.15
    stroke_width: 2
    data_generator: |
      return entity.attributes.data_series.map((e) => [new Date(e.dateTime).getTime(), e.value]);
  - entity: sensor.stromgedacht_70173_residuallast
    name: Residuallast
    yaxis_id: power
    color: "#ff7f0e"
    stroke_width: 2
    data_generator: |
      return entity.attributes.data_series.map((e) => [new Date(e.dateTime).getTime(), e.value]);
  - entity: sensor.stromgedacht_70173_supergrun_schwelle
    name: Supergrün-Schwelle
    yaxis_id: power
    color: "#00c853"
    stroke_width: 2
    stroke_dash: 4
    show:
      in_header: false
    data_generator: |
      return entity.attributes.data_series.map((e) => [new Date(e.dateTime).getTime(), e.value]);
```

Ersetze `70173` durch deine Postleitzahl und prüfe die Entitäts-IDs unter **Einstellungen** > **Geräte & Dienste** > **StromGedacht**.

### Kommende Zustände als Liste

Eine Markdown-Karte zeigt die kommenden Ampel-Zustände:

```yaml
type: markdown
title: StromGedacht
content: |
  {% set names = {"super_green": "🌱 Supergrün", "green": "✅ Grün", "orange": "🟠 Orange", "red": "🔴 Rot"} %}
  {% set codes = {-1: "super_green", 1: "green", 3: "orange", 4: "red"} %}
  {% for s in state_attr("sensor.stromgedacht_70173_status", "future_states") or [] %}
  - {{ as_timestamp(s.from) | timestamp_custom("%a %H:%M") }} – {{ as_timestamp(s.to) | timestamp_custom("%a %H:%M") }}: {{ names[codes[s.state]] }}
  {% endfor %}
  **Beste Zeit:** {{ as_timestamp(states("sensor.stromgedacht_70173_beste_verbrauchszeit"), 0) | timestamp_custom("%a %H:%M") }}
```

## 🤖 Automationen

### Geräte-Auslöser

Wähle im Automationseditor **Gerät** als Auslöser, dann dein StromGedacht-Gerät und einen der Auslöser, z.B. **Netzstatus wird Supergrün**. Optional kann eine Dauer angegeben werden.

### Beispiele

Verbraucher bei Supergrün einschalten:

```yaml
triggers:
  - trigger: state
    entity_id: sensor.stromgedacht_70173_status
    to: "super_green"
actions:
  - action: switch.turn_on
    target:
      entity_id: switch.waermepumpe_boost
```

Spülmaschine zur besten Zeit starten (die Zeit wird mit jeder Prognose aktualisiert):

```yaml
triggers:
  - trigger: time
    at: sensor.stromgedacht_70173_beste_verbrauchszeit
conditions:
  - condition: state
    entity_id: input_boolean.spuelmaschine_bereit
    state: "on"
actions:
  - action: switch.turn_on
    target:
      entity_id: switch.spuelmaschine
```

Eine Stunde vor einer Verbrauchsreduzierung warnen:

```yaml
triggers:
  - trigger: time
    at:
      entity_id: sensor.stromgedacht_70173_nachste_verbrauchsreduzierung
      offset: "-01:00:00"
actions:
  - action: notify.notify
    data:
      message: >
        StromGedacht: Verbrauch reduzieren von
        {{ as_timestamp(states("sensor.stromgedacht_70173_nachste_verbrauchsreduzierung")) | timestamp_custom("%H:%M") }}
        bis {{ as_timestamp(state_attr("sensor.stromgedacht_70173_nachste_verbrauchsreduzierung", "end")) | timestamp_custom("%H:%M") }} Uhr.
```

---

**Hinweis:** Dies ist ein privates Projekt und kein offizielles Produkt der TransnetBW GmbH. Daten von der [StromGedacht API](https://api.stromgedacht.de).
