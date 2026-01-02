# StromGedacht für Home Assistant

> [🇬🇧 English Description](README.md)

Diese Custom Integration bindet die [StromGedacht API](https://api.stromgedacht.de) (von TransnetBW) in Home Assistant ein. Sie liefert Informationen über den aktuellen Status des Stromnetzes in Baden-Württemberg, einschließlich Warnungen zur Verbrauchsreduzierung oder Hinweise zur Nutzung von Überschussstrom.

## ✨ Funktionen

* **Einfache Einrichtung:** Konfiguration komplett über die Benutzeroberfläche (UI).
* **PLZ-basiert:** Lokalisierte Daten für deinen Standort.
* **Echtzeit-Status:** Ampelsystem (Grün/Gelb/Rot/Supergrün).
* **Leistungsdaten:** Sensoren für **Netzlast**, **Erneuerbare Energie** und **Residuallast** (in MW).
* **Anpassbar:** Das Aktualisierungsintervall kann in den Optionen geändert werden.

## 📥 Installation

### Option 1: HACS (Empfohlen)

1.  Öffne HACS in Home Assistant.
2.  Gehe zu **Integrationen** > Menü oben rechts (3 Punkte) > **Benutzerdefinierte Repositorys**.
3.  Füge die URL hinzu: `https://github.com/V4n1X/ha_stromgedacht`
4.  Kategorie: **Integration**.
5.  Klicke auf **Hinzufügen**.
6.  Suche in HACS nach **StromGedacht** und installiere es.
7.  Starte Home Assistant neu.

### Option 2: Manuell

1.  Lade das neueste Release herunter.
2.  Kopiere den Ordner `stromgedacht` (aus `custom_components`) in dein Home Assistant Verzeichnis: `config/custom_components/`.
3.  Starte Home Assistant neu.

## ⚙️ Konfiguration

1.  Gehe zu **Einstellungen** > **Geräte & Dienste**.
2.  Klicke auf **Integration hinzufügen**.
3.  Suche nach **StromGedacht**.
4.  Gib deine **Postleitzahl** ein (z.B. `70173`).
5.  (Optional) Passe das Abrufintervall an.

## 📊 Entitäten & Status

### Sensoren
Die Integration erstellt folgende Sensoren:
* **Status:** Das Ampelsystem als Textzustand.
* **Netzlast:** Aktueller Stromverbrauch im Netz (MW).
* **Erneuerbare Energie:** Aktuelle Erzeugung aus Wind/Sonne (MW).
* **Residuallast:** Differenz aus Last und Erneuerbaren (MW).

### Bedeutung der Zustände
Der Status-Sensor folgt der offiziellen Logik der StromGedacht-App:

| Wert | Status | Bedeutung |
| :--- | :--- | :--- |
| **-1** | **Supergrün** | 🍃 Strom jetzt nutzen, um die Netzdienlichkeit zu unterstützen. |
| **1** | **Grün** | ✅ Normalbetrieb – Du musst nichts weiter tun. |
| **3** | **Orange** | ⚠️ Verbrauch reduzieren, um Kosten und CO2 zu sparen. |
| **4** | **Rot** | ⚡ Verbrauch reduzieren, um Strommangel zu verhindern. |

---

**Hinweis:** Dies ist ein privates Projekt und kein offizielles Produkt der TransnetBW GmbH.
