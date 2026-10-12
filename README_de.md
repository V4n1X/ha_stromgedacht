<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="images/stromgedacht_logo_dark.svg">
    <img src="images/stromgedacht_logo.svg" alt="StromGedacht" width="420">
  </picture>
</p>

<h1 align="center">StromGedacht für Home Assistant</h1>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Default-41BDF5.svg" alt="HACS Default"></a>
  <a href="https://github.com/V4n1X/ha_stromgedacht/releases"><img src="https://img.shields.io/github/v/release/V4n1X/ha_stromgedacht" alt="GitHub release"></a>
  <a href="https://github.com/V4n1X/ha_stromgedacht/actions/workflows/tests.yaml"><img src="https://github.com/V4n1X/ha_stromgedacht/actions/workflows/tests.yaml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/V4n1X"><img src="https://img.shields.io/badge/maintainer-V4n1X-blue" alt="Maintainer"></a>
</p>

<p align="center">
  <a href="README.md">🇬🇧 English Description</a>
</p>

Diese Custom Integration bringt [StromGedacht](https://www.stromgedacht.de), die Netz-Ampel des Übertragungsnetzbetreibers TransnetBW, in Home Assistant. Sie zeigt den aktuellen und kommenden Zustand des Stromnetzes in Baden-Württemberg und hilft dir, deinen **Verbrauch zu verschieben** – hin zu Zeiten mit viel erneuerbarer Energie und weg von Zeiten, in denen das Netz unter Druck steht.

## Inhalt

- [Funktionen](#-funktionen)
- [Installation](#-installation)
- [Konfiguration](#-konfiguration)
- [Entitäten](#-entitäten)
- [Verbrauch planen](#-verbrauch-planen)
- [Automationen](#-automationen)
- [Fehlerbehebung](#-fehlerbehebung)
- [Entwicklung](#-entwicklung)

## ✨ Funktionen

- **Netz-Ampel:** Aktueller Zustand des Stromnetzes (Supergrün / Grün / Orange / Rot) für deine Postleitzahl.
- **Vorschau:** Kommende Zustände der nächsten 48 Stunden sowie der Beginn des **nächsten Supergrün**- und des **nächsten Verbrauchsreduzierungs**-Zeitraums.
- **Beste Verbrauchszeit:** Der Zeitpunkt mit der niedrigsten Residuallast (höchster Anteil Erneuerbarer) in der Prognose.
- **Prognosedaten:** Netzlast, Erneuerbare Energie, Residuallast und Supergrün-Schwelle in MW, inklusive Prognoseverlauf für Diagramme.
- **Automationen:** Geräte-Auslöser wie *„Netzstatus wird Supergrün“* und Zeitstempel-Sensoren als Zeit-Auslöser.
- **Einrichtung per UI:** Kein YAML nötig, auf Deutsch und Englisch übersetzt.

## 📸 Vorschau

<p align="left">
  <img src="https://github.com/user-attachments/assets/f12b0c5e-2115-40ba-b548-47548c1bc120" alt="StromGedacht Dashboard Beispiel" width="600">
</p>

## 📦 Installation

Voraussetzung ist Home Assistant **2025.8** oder neuer.

### HACS (empfohlen)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=V4n1X&repository=ha_stromgedacht&category=Integration)

1. Öffne HACS in Home Assistant.
2. Suche nach **StromGedacht** und installiere es.
3. Starte Home Assistant neu.

### Manuell

1. Lade das neueste [Release](https://github.com/V4n1X/ha_stromgedacht/releases) herunter.
2. Kopiere den Ordner `custom_components/stromgedacht` in das Verzeichnis `config/custom_components/` deines Home Assistant.
3. Starte Home Assistant neu.

## 🔧 Konfiguration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=stromgedacht)

1. Gehe zu **Einstellungen** > **Geräte & Dienste**.
2. Klicke auf **Integration hinzufügen** und suche nach **StromGedacht**.
3. Gib deine Postleitzahl ein und passe bei Bedarf die Optionen an.

| Option | Beschreibung | Standard |
| :--- | :--- | :--- |
| **Postleitzahl** | Deutsche Postleitzahl (5-stellig) im Netzgebiet der TransnetBW | – |
| **Abrufintervall** | Wie oft die Daten abgerufen werden, in Minuten (mindestens 5) | `15` |
| **Kurzer Statustext** | Nur die Farbe anzeigen (z.B. „Grün“) statt der ausführlichen Beschreibung | aus |

Abrufintervall und Statustext lassen sich später über **Konfigurieren** an der Integration ändern. Für mehrere Postleitzahlen fügst du die Integration einfach mehrmals hinzu.

## 📊 Entitäten

Alle Entitäten gehören zu einem Gerät pro Postleitzahl.

> [!NOTE]
> Die Entitäts-IDs hängen von der Sprache deiner Home-Assistant-Installation ab. Die Beispiele in dieser Anleitung verwenden deutsche Entitäts-IDs mit der Postleitzahl `70173`, z.B. `sensor.stromgedacht_70173_residuallast`. Auf Englisch heißt sie `sensor.stromgedacht_70173_residual_load`. Deine Entitäts-IDs findest du auf der Geräteseite der Integration.

### Status

| Entität | Beschreibung | Attribute |
| :--- | :--- | :--- |
| `sensor.stromgedacht_70173_status` | Die Netz-Ampel | `description`, `future_states` (kommende Zustände der nächsten 48 h), `zip_code` |

| API-Wert | Zustand | Bedeutung |
| :--- | :--- | :--- |
| -1 | `super_green` | 🌱 Strom jetzt nutzen, um die Netzdienlichkeit zu unterstützen. |
| 1 | `green` | ✅ Normalbetrieb – Du musst nichts weiter tun. |
| 3 | `orange` | 🟠 Verbrauch reduzieren, um Kosten und CO2 zu sparen. |
| 4 | `red` | 🔴 Verbrauch reduzieren, um Strommangel zu verhindern. |

Die Option „Kurzer Statustext“ ändert nur den angezeigten Text. In Automationen gelten immer die Zustände aus der Tabelle.

### Planung

| Entität | Beschreibung | Attribute |
| :--- | :--- | :--- |
| `sensor.stromgedacht_70173_beste_verbrauchszeit` | Beginn des 15-Minuten-Abschnitts mit der niedrigsten Residuallast bis zum Ende der Prognose | `residual_load`, `forecast_until` |
| `sensor.stromgedacht_70173_nachstes_supergrun` | Beginn des aktuellen oder nächsten Supergrün-Zeitraums | `end`, `state` |
| `sensor.stromgedacht_70173_nachste_verbrauchsreduzierung` | Beginn des aktuellen oder nächsten orangen oder roten Zeitraums | `end`, `state` (`orange` oder `red`) |

Das sind Zeitstempel-Sensoren. Sie sind `unknown`, wenn kein solcher Zeitraum bzw. keine Prognose vorliegt. Läuft ein Zeitraum bereits, zeigt der Sensor dessen Beginn in der Vergangenheit, und das Attribut `end` verrät, wie lange er noch dauert.

### Prognose

| Entität | Beschreibung | Attribute |
| :--- | :--- | :--- |
| `sensor.stromgedacht_70173_netzlast` | Aktuelle Netzlast in MW | `data_series` |
| `sensor.stromgedacht_70173_erneuerbare_energie` | Aktuelle Erzeugung aus Erneuerbaren in MW | `data_series` |
| `sensor.stromgedacht_70173_residuallast` | Netzlast abzüglich erneuerbarer Erzeugung in MW | `data_series` |
| `sensor.stromgedacht_70173_supergrun_schwelle` | Schwelle von StromGedacht für den Zustand Supergrün in MW | `data_series` |

`data_series` enthält die 15-Minuten-Werte von vor zwei Stunden bis zum Ende der Prognose (meist Ende des Folgetags), jeweils als `{"dateTime": ..., "value": ...}`. Die Attribute `future_states` und `data_series` werden nicht in der Recorder-Datenbank gespeichert, damit diese klein bleibt.

## 🔮 Verbrauch planen

Die Ampel sagt dir, was du *jetzt* tun solltest. Um zu entscheiden, *wann* flexible Verbraucher wie Spülmaschine, Waschmaschine, E-Auto oder Wärmepumpe laufen sollen, hilft die **Residuallast**: der Teil des Verbrauchs, der nicht durch erneuerbare Energie gedeckt ist. Je niedriger sie ist, desto grüner ist dein Strom. Anders als ein bundesweiter EPEX-Preischart gelten diese Werte speziell für das Netzgebiet der TransnetBW.

- **Beste Verbrauchszeit** nennt dir direkt den besten Zeitpunkt in der Prognose.
- **Nächstes Supergrün** und **Nächste Verbrauchsreduzierung** zeigen, wann die nächsten Zeiträume beginnen und enden.
- Die Prognose-Sensoren liefern die kompletten Verläufe für Diagramme.

### Prognose-Diagramm

Mit der [ApexCharts Card](https://github.com/RomRider/apexcharts-card) (über HACS erhältlich) bekommst du ein Prognose-Diagramm ähnlich der StromGedacht-App:

<details>
<summary>Konfiguration der Karte</summary>

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

</details>

### Kommende Zustände

Eine Markdown-Karte listet die kommenden Ampel-Zustände und die beste Verbrauchszeit auf:

<details>
<summary>Konfiguration der Karte</summary>

```yaml
type: markdown
title: StromGedacht
content: |
  {%- set names = {"super_green": "🌱 Supergrün", "green": "✅ Grün", "orange": "🟠 Orange", "red": "🔴 Rot"} %}
  {%- set codes = {-1: "super_green", 1: "green", 3: "orange", 4: "red"} %}
  {%- for s in state_attr("sensor.stromgedacht_70173_status", "future_states") or [] %}
  - {{ as_timestamp(s.from) | timestamp_custom("%a %H:%M") }} – {{ as_timestamp(s.to) | timestamp_custom("%a %H:%M") }}: {{ names[codes[s.state]] }}
  {%- endfor %}

  **Beste Zeit:** {{ as_timestamp(states("sensor.stromgedacht_70173_beste_verbrauchszeit"), 0) | timestamp_custom("%a %H:%M") }}
```

</details>

## 🤖 Automationen

### Geräte-Auslöser

Wähle im Automationseditor **Gerät** als Auslöser, dann dein StromGedacht-Gerät und einen der Auslöser, z.B. **Netzstatus wird Supergrün**. Optional kann eine Dauer angegeben werden.

### Beispiele

<details>
<summary>Verbraucher bei Supergrün einschalten</summary>

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

</details>

<details>
<summary>Spülmaschine zur besten Zeit starten</summary>

Die beste Zeit wird mit jeder Prognose aktualisiert, die Automation nutzt also immer die neueste Prognose.

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

</details>

<details>
<summary>Eine Stunde vor einer Verbrauchsreduzierung warnen</summary>

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

</details>

## ❓ Fehlerbehebung

**„StromGedacht liefert für diese Postleitzahl keine Daten“**
StromGedacht deckt nur das Netzgebiet der TransnetBW ab, also überwiegend Baden-Württemberg.

**Die Beispiele funktionieren mit meinen Entitäten nicht**
Prüfe die Entitäts-IDs auf der Geräteseite der Integration, sie hängen von der Sprache deines Home Assistant ab (siehe [Entitäten](#-entitäten)).

**Ein Planungs-Sensor zeigt eine Zeit in der Vergangenheit**
Der Zeitraum läuft bereits, das Attribut `end` zeigt, wann er endet. Die Planungs-Sensoren werden bei jedem Abruf neu berechnet. Nach dem Ende eines Zeitraums kann es daher bis zu einem Abrufintervall dauern, bis der nächste angezeigt wird.

**Alle Sensoren sind nicht verfügbar**
Die StromGedacht API war nicht erreichbar. Die Integration versucht es beim nächsten Abruf automatisch erneut. Details stehen im Home-Assistant-Log.

## 🧪 Entwicklung

Die Tests laufen gegen die in `requirements_test.txt` festgelegte Home-Assistant-Version (Linux oder WSL, Home Assistant läuft nicht unter Windows):

```bash
pip install -r requirements_test.txt
python -m pytest
```

Issues und Pull Requests sind willkommen.

## 📄 Lizenz & Hinweis

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).

Dies ist ein privates Projekt und kein offizielles Produkt der TransnetBW GmbH. Daten von der [StromGedacht API](https://api.stromgedacht.de). Name und Logo von StromGedacht gehören der TransnetBW GmbH.
