<div align="center">

# 👨‍👩‍👧‍👦 Custody Schedule

**Home Assistant integration for intelligent shared custody management**

[![Version](https://img.shields.io/badge/version-1.8.40-blue.svg)](https://github.com/Jackngl/custody/releases)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.12-green.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

<img src="icon.png" alt="Custody Schedule Icon" width="128"/>

[🇫🇷 Version française](README.fr.md) | [🇬🇧 English version](README.md)

</div>

---

## 📖 About

**Custody Schedule** is a complete Home Assistant integration that simplifies shared custody management. It automates custody period calculations, syncs with your calendar, and enables smart home automation based on children's presence.

### ✨ Why Custody Schedule?

- 🎯 **Intuitive Configuration** : Step-by-step guided interface
- 🤖 **Complete Automation** : Smart period calculation and school holiday management
- 📅 **Calendar Sync** : Native integration with Google Calendar
- 🏠 **Smart Home Automation** : Control heating, lights, notifications based on presence
- 🌍 **International Support** : French, Belgian, Swiss, Luxembourg, and Quebec school zones
- 🗣️ **Voice Assistants** : Compatible with Alexa and Home Assistant Assist

---

## 🚀 Quick Start

### Installation via HACS (Recommended)

1. **Install HACS** if needed: [HACS Documentation](https://hacs.xyz/docs/setup/download)

2. **Add the repository**:
   
   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Jackngl&repository=custody&category=integration)
   
   *Or add manually*: `https://github.com/Jackngl/custody` in **HACS** > **Custom repositories**

3. **Install and restart**:
   - Click **Download** in HACS
   - Restart Home Assistant

4. **Configure**:
   - **Settings** → **Devices & Services** → **Add Integration**
   - Search for "Custody" and follow the configuration wizard

### Manual Installation

```bash
cd /config
git clone https://github.com/Jackngl/custody.git
cp -r custody/custom_components/custody_schedule /config/custom_components/
```

Restart Home Assistant then add the integration via the interface.

---

## ✨ Main Features

### 🎛️ Simplified Configuration

- Guided workflow with clear labels (child ➜ custody ➜ holidays ➜ options)
- Intuitive and complete user interface
- Multi-child support with independent configurations

### 🧮 Smart Calculation

- **Custody Patterns**:
  - Alternate weeks (1/1)
  - Alternate weekends
  - Custom pattern (day-by-day selection over 14 days)
  - 2-2-3 or 2-2-5-5 patterns
  - Exceptions and custom rules (fixed dates)

- **Holiday Management**:
  - Automatic holiday alternation each year
  - Priority management (holidays and parental holidays properly split regular weekends)
  - Flexible rules: 1st/2nd week, halves, even/odd weeks, July/August
  - Automatic Mother's Day and Father's Day management

### 🌍 International Support

- **French School Zones** : A, B, C, Corsica, DOM-TOM
- **Official API** : `data.education.gouv.fr` for school holidays
- **Multi-country Support** : Belgium, Switzerland, Luxembourg, Quebec
- **Customizable API URL** for alternative sources
- **Built-in Test Service** to diagnose issues

### 🔗 Integrations

- **Google Calendar Sync** : Automatic event creation and deletion
- **Integrated Calendar** : Complete visualization of custody periods
- **Home Assistant Events** : Triggers for automations
- **Dedicated Services** : Exceptions, force presence/absence, recalculation

### 🎙️ Voice Assistants

- **Amazon Alexa** : Blueprints for automatic announcements
- **Home Assistant Assist** : Natural language questions about presence
- **Bilingual Support** : French and English

---

## ⚙️ Configuration

Configuration is done entirely through the Home Assistant user interface.

### Configuration Steps

1. **Child Information** : Name, icon, photo
2. **Custody Type** : Select pattern (alternate week, weekend, etc.)
3. **School Zone and Holidays** : Zone (A/B/C/Corsica/DOM-TOM) and holiday rules
4. **Advanced Options** :
   - Custom notes
   - Notifications
   - Calendar sync (Google Calendar)
   - Target calendar + sync window
   - Sync interval
   - Exceptions (advanced UI)
   - Custom API URL (optional)

### Google Calendar Synchronization

Enable synchronization to automatically create custody events on your Home Assistant calendar.

**Configuration**:
1. **Settings** → **Devices & Services** → **Custody** → **Options**
2. Select **Advanced Options**
3. Enable **Google Calendar Synchronization**
4. Choose the **Target Calendar**
5. Set the **Sync Window** (default: 120 days)
6. Set the **Sync Interval** (default: 1 hour)

### Exceptions

Manage exceptions (additional days, weekday custody, etc.) via the interface:

1. **Settings** → **Devices & Services** → **Custody** → **Options**
2. Select **Exceptions**
3. Add, modify, or delete an exception (start + end + title)

#### Recurring Exceptions

In the same screen, manage recurring exceptions (weekly):
- Day of the week + start/end time
- Optional: start date / end date

Exceptions (one-time and recurring) appear in the integration calendar.

### API URL Configuration

To use an alternative API for school holidays:

1. **Settings** → **Devices & Services** → **Custody** → **Options**
2. Select **Advanced Options**
3. Enter your custom URL in **School Holiday API URL**
   - The URL must contain placeholders `{year}` and `{zone}`
   - Example: `https://api.example.com/holidays?year={year}&zone={zone}`

---

## 🛠️ Diagnostics and Cleanup (Purge)

If you notice duplicates or events that don't delete correctly in your Google Calendar, use the robust purge service.

Since version 1.3.0, purge uses a direct access method to Home Assistant entities to retrieve real identifiers (UID).

### Manual Purge

1. Go to **Developer Tools** → **Services** (or Actions)
2. Select `Custody: Purge Google Events` (service `custody_schedule.purge_calendar_events`)
3. Switch to **YAML mode** and use:

```yaml
action: custody_schedule.purge_calendar_events
data:
  entry_id: "YOUR_ENTRY_ID"
  days: 120
  debug: true
```

> [!TIP]
> To find your `entry_id`, use this template in HA's Template tool:
> `{{ config_entry_id('binary_sensor.CHILD_NAME_presence') }}`

---

## 🎨 Dashboards (Lovelace)

### Mushroom Card (Recommended 🌟)

This card changes color and icon based on child presence.

```yaml
type: custom:mushroom-template-card
primary: |-
  {% if is_state('binary_sensor.lucas_presence', 'on') %}
    Lucas is home
  {% else %}
    Lucas is with the other parent
  {% endif %}
secondary: |-
  {% if is_state('binary_sensor.lucas_presence', 'on') %}
    Departure: {{ states('sensor.lucas_next_departure') }}
  {% else %}
    Return: {{ states('sensor.lucas_next_arrival') }}
  {% endif %}
icon: |-
  {% if is_state('binary_sensor.lucas_presence', 'on') %}
    mdi:home-heart
  {% else %}
    mdi:home-export-outline
  {% endif %}
icon_color: |-
  {% if is_state('binary_sensor.lucas_presence', 'on') %}
    blue
  {% else %}
    grey
  {% endif %}
tap_action:
  action: navigate
  navigation_path: /config/devices/dashboard
```

### Minimalist Status Badge

Ideal for a condensed view at the top of the dashboard.

```yaml
type: custom:mushroom-chips-card
chips:
  - type: template
    content: "Lucas: {{ states('sensor.lucas_days_remaining') }}d"
    icon: mdi:account-clock
    icon_color: "{{ 'green' if is_state('binary_sensor.lucas_presence', 'on') else 'orange' }}"
    tap_action:
      action: more-info
      entity: binary_sensor.lucas_presence
```

---

## 🔧 Available Services

### `custody_schedule.set_manual_dates`

Adds one-time presence periods (holidays, specific exchanges).

**Parameters**:
- `entry_id` (required): Integration ID
- `dates` (required): List of periods with `start`, `end`, and optionally `label`

**Example**:
```yaml
action: custody_schedule.set_manual_dates
data:
  entry_id: "1234567890abcdef1234567890abcdef"
  dates:
    - start: "2024-07-15T08:00:00+02:00"
      end: "2024-07-22T19:00:00+02:00"
      label: "Holidays at dad's"
```

### `custody_schedule.override_presence`

Forces present/absent state for a given duration.

**Parameters**:
- `entry_id` (required): Integration ID
- `state` (required): `on` (present) or `off` (absent)
- `duration` (optional): Duration in minutes

**Example**:
```yaml
action: custody_schedule.override_presence
data:
  entry_id: "1234567890abcdef1234567890abcdef"
  state: "on"
  duration: 120  # 2 hours
```

### `custody_schedule.refresh_schedule`

Triggers an immediate schedule recalculation.

**Parameters**:
- `entry_id` (required): Integration ID

**Example**:
```yaml
action: custody_schedule.refresh_schedule
data:
  entry_id: "1234567890abcdef1234567890abcdef"
```

### `custody_schedule.test_holiday_api`

Tests the connection to the school holiday API and displays results in logs.

**Parameters**:
- `entry_id` (optional): Integration ID (uses this integration's config)
- `zone` (optional, default: "A"): School zone to test
- `year` (optional): School year in format "2024-2025"

**Example**:
```yaml
action: custody_schedule.test_holiday_api
data:
  entry_id: "1234567890abcdef1234567890abcdef"
  zone: "C"
  year: "2024-2025"
```

### `custody_schedule.export_exceptions`

Exports exceptions (one-time + recurring) to a JSON file in `/config/www`.

**Parameters**:
- `entry_id` (required): Integration ID
- `filename` (optional): Filename (e.g., `custody_exceptions.json`)

**Example**:
```yaml
action: custody_schedule.export_exceptions
data:
  entry_id: "1234567890abcdef1234567890abcdef"
  filename: "custody_exceptions.json"
```

### `custody_schedule.import_exceptions`

Imports exceptions from a JSON file or direct payload.

**Parameters**:
- `entry_id` (required): Integration ID
- `filename` (optional): Filename in `/config/www`
- `exceptions` (optional): List of one-time exceptions
- `recurring` (optional): List of recurring exceptions

**Example**:
```yaml
action: custody_schedule.import_exceptions
data:
  entry_id: "1234567890abcdef1234567890abcdef"
  filename: "custody_exceptions.json"
```

### `custody_schedule.purge_calendar_events`

Manually deletes calendar events. This method identifies events created by Custody even when orphaned or duplicated.

**Parameters**:
- `entry_id` (required): Integration ID
- `days` (optional): Scan window in days (default: 120)
- `include_unmarked` (optional): Attempts to delete even events without explicit marker
- `purge_all` (optional): Deletes absolutely ALL found events (warning)
- `match_text` (optional): Deletes events containing this text in summary
- `debug` (optional): Displays technical details in logs (recommended)

**Example**:
```yaml
action: custody_schedule.purge_calendar_events
data:
  entry_id: "01KF1ZW5K8JNX55258QBCF1STF"
  debug: true
```

---

## 📡 Home Assistant Events

The integration automatically emits events to trigger automations:

### `custody_arrival`

Triggered when the child arrives (transition from `off` to `on`).

**Data**:
- `entry_id`: Integration ID
- `child`: Child's name
- `next_departure`: Next departure (ISO format)
- `next_arrival`: Next arrival (ISO format)

### `custody_departure`

Triggered when the child leaves (transition from `on` to `off`).

**Data**:
- `entry_id`: Integration ID
- `child`: Child's name
- `next_departure`: Next departure (ISO format)
- `next_arrival`: Next arrival (ISO format)

### `custody_vacation_start`

Triggered at the start of school holidays.

**Data**:
- `entry_id`: Integration ID
- `holiday`: Holiday period name

### `custody_vacation_end`

Triggered at the end of school holidays.

**Data**:
- `entry_id`: Integration ID
- `holiday`: Name of the ending holiday period

---

## 📊 Generated Entities

For each configured child, the following entities are automatically created:

| Entity | Type | Description |
|--------|------|-------------|
| `binary_sensor.<name>_presence` | Binary Sensor | Present/absent state (`on`/`off`) |
| `device_tracker.<name>_tracker` | Device Tracker | Presence tracking (`home`/`not_home`) |
| `sensor.<name>_next_arrival` | Sensor | Next arrival (datetime) |
| `sensor.<name>_next_departure` | Sensor | Next departure (datetime) |
| `sensor.<name>_days_remaining` | Sensor | Days remaining before next change |
| `sensor.<name>_current_period` | Sensor | Current period (`school`/`vacation`) |
| `sensor.<name>_next_vacation_name` | Sensor | Next school holidays |
| `sensor.<name>_next_vacation_start` | Sensor | Next holiday start date |
| `sensor.<name>_days_until_vacation` | Sensor | Days until holidays |
| `calendar.<name>_calendar` | Calendar | Calendar with all periods |

> **Note**: `<name>` corresponds to the child's name normalized to lowercase with spaces replaced by underscores. `entity_id` are always in English (ASCII only), even if the display name contains accents.
>
> **Examples**:
> - "Lucas" → `binary_sensor.lucas_presence`, `calendar.lucas_calendar`
> - "Sarah-Léa" → `binary_sensor.sarah_lea_presence`, `calendar.sarah_lea_calendar`
> - "François" → `binary_sensor.francois_presence`, `calendar.francois_calendar`

Display names in the Home Assistant interface are localized according to the configured language (French/English) and preserve the original name characters.

**Available Attributes**:
- `vacation_name`: Name of current holiday period
- `zone`: Configured school zone
- `location`: Configured location
- `notes`: Configured notes

---

## 🤖 Automations and Examples

### 1. Adjust Heating Based on Presence

```yaml
automation:
  - alias: "Child room heating"
    description: "Adjusts heating based on child presence"
    trigger:
      - platform: state
        entity_id: binary_sensor.lucas_presence
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: climate.lucas_room
        data:
          preset_mode: "{{ 'comfort' if trigger.to_state.state == 'on' else 'eco' }}"
      - service: climate.set_temperature
        target:
          entity_id: climate.lucas_room
        data:
          temperature: "{{ 20 if trigger.to_state.state == 'on' else 16 }}"
```

### 2. Notification Before Arrival

```yaml
automation:
  - alias: "Child arrival notification"
    description: "Notifies 1 day before arrival"
    trigger:
      - platform: numeric_state
        entity_id: sensor.lucas_days_remaining
        below: 1
        above: 0
    condition:
      - condition: state
        entity_id: binary_sensor.lucas_presence
        state: "off"
    action:
      - service: notify.mobile_app_phone
        data:
          message: "Lucas arrives tomorrow! Don't forget to prepare his room."
          title: "Scheduled Arrival"
```

### 3. Turn On Lights on Arrival

```yaml
automation:
  - alias: "Lights on arrival"
    description: "Turns on lights when child arrives"
    trigger:
      - platform: event
        event_type: custody_arrival
        event_data:
          entry_id: "1234567890abcdef1234567890abcdef"
    action:
      - service: light.turn_on
        target:
          entity_id: light.lucas_room
        data:
          brightness: 200
          color_temp: 370
```

### 4. Turn Off Devices on Departure

```yaml
automation:
  - alias: "Energy saving on departure"
    description: "Turns off devices when child leaves"
    trigger:
      - platform: event
        event_type: custody_departure
        event_data:
          entry_id: "1234567890abcdef1234567890abcdef"
    action:
      - service: light.turn_off
        target:
          entity_id: 
            - light.lucas_room
            - light.lucas_study
      - service: climate.set_preset_mode
        target:
          entity_id: climate.lucas_room
        data:
          preset_mode: "away"
```

### 5. Holiday Start Notification

```yaml
automation:
  - alias: "Holiday start notification"
    description: "Notifies at start of school holidays"
    trigger:
      - platform: event
        event_type: custody_vacation_start
        event_data:
          entry_id: "1234567890abcdef1234567890abcdef"
    action:
      - service: notify.mobile_app_phone
        data:
          message: "The {{ trigger.event.data.holiday }} holidays are starting!"
          title: "School Holidays"
```

### 6. Conditional Dashboard

```yaml
type: entities
title: Custody
entities:
  - entity: binary_sensor.lucas_presence
    name: Presence
  - entity: sensor.lucas_next_arrival
    name: Next arrival
  - entity: sensor.lucas_next_departure
    name: Next departure
  - entity: sensor.lucas_days_remaining
    name: Days remaining
  - entity: sensor.lucas_current_period
    name: Period
  - type: custom:auto-entities
    card:
      type: entities
      title: "Details"
    filter:
      include:
        - entity_id: sensor.lucas_*
          attributes:
            - vacation_name
            - zone
            - location
```

### 7. Script to Force Temporary Presence

```yaml
script:
  temporary_presence:
    alias: "Force temporary presence"
    sequence:
      - service: custody_schedule.override_presence
        data:
          entry_id: "1234567890abcdef1234567890abcdef"
          state: "on"
          duration: 180  # 3 hours
      - service: notify.mobile_app_phone
        data:
          message: "Presence forced for 3 hours"
```

### 8. Automation Based on Remaining Days

```yaml
automation:
  - alias: "Prepare room 2 days before"
    description: "Activates heating 2 days before arrival"
    trigger:
      - platform: numeric_state
        entity_id: sensor.lucas_days_remaining
        below: 2.5
        above: 1.5
    condition:
      - condition: state
        entity_id: binary_sensor.lucas_presence
        state: "off"
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: climate.lucas_room
        data:
          preset_mode: "comfort"
```

---

## 🎙️ Voice Assistants

### Amazon Alexa

Use a **Blueprint** to have Alexa automatically announce custody changes on your speakers (Echo, Dot, etc.).

**Configuration**:
1. Download `alexa_custody_announcement.yaml` from the `blueprints` folder
2. Place it in `/config/blueprints/automation/`
3. **Settings** → **Automations & Scenes** → **Blueprints**
4. Create an automation from the "Alexa Announcement - Custody Change" template

### Home Assistant Assist

Thanks to the `presence` device class on binary sensors, ask natural questions:
- *"Is Lucas present?"*
- *"What is Lucas's presence status?"*

> [!TIP]
> For a better experience with Alexa, expose the `binary_sensor.<name>_presence` entity via Nabu Casa or your manual Alexa integration.

---

## 🌐 School Holiday API

The integration uses the official French Ministry of Education API (`data.education.gouv.fr`) to automatically retrieve school holiday dates.

### Features

- ✅ Automatic holiday retrieval by zone (A, B, C, Corsica, DOM-TOM)
- ✅ School year management (format "2024-2025")
- ✅ Smart cache to reduce API calls
- ✅ Multi-entry support with different API URLs
- ✅ Test service to diagnose issues

### Supported Zones

- **Zone A**: Besançon, Bordeaux, Clermont-Ferrand, Dijon, Grenoble, Limoges, Lyon, Poitiers
- **Zone B**: Aix-Marseille, Amiens, Lille, Nancy-Metz, Nantes, Nice, Normandy, Orléans-Tours, Reims, Rennes, Strasbourg
- **Zone C**: Créteil, Montpellier, Paris, Toulouse, Versailles
- **Corsica**: Corsica
- **DOM-TOM**: Guadeloupe (default), Martinique, French Guiana, Réunion, Mayotte

### API Customization

You can configure a custom API URL in advanced options. The URL must contain placeholders `{year}` and `{zone}`.

**Expected Format**:
```
https://api.example.com/holidays?year={year}&zone={zone}
```

### Test the API

Use the `custody_schedule.test_holiday_api` service to test the connection:

```yaml
service: custody_schedule.test_holiday_api
data:
  zone: "A"
  year: "2024-2025"
```

Results are available in Home Assistant logs (**Settings** → **System** → **Logs**).

---

## 🗺️ Roadmap

### v1.0 ✅
- [x] Complete UI configuration
- [x] Automatic period calculation
- [x] School holiday API
- [x] Services and events
- [x] Multi-child support
- [x] Customizable API URL
- [x] API test service

### v1.1 ✅
- [x] Advanced calendar with monthly view
- [x] Google Calendar synchronization
- [x] Native Home Assistant notifications
- [x] Advanced exception management
- [x] PDF schedule export

### v1.5 ✅
- [x] Lovelace Dashboards "Ready-to-use" (Premium examples)
- [x] Regional holiday support (Alsace-Moselle)
- [x] Complete French localization
- [x] Automatic startup log cleanup

### v1.7 ✅
- [x] **Voice Support**: Optimized support for **Amazon Alexa**
- [x] **Blueprints**: Added first Alexa announcement template
- [x] **Assist Refinements**: Custom sentences ("Who has Lucas?")

### v1.8 (Available 🚀)
- [x] **Bilingual Support**: Complete French / English translations (Entities, Config Flow, Assist)
- [x] **Internationalization**: Support for school calendars and holidays for Belgium, Switzerland, Luxembourg, and Quebec
- [x] **Language Detection**: Automatic adaptation based on HA configuration for Assist

### v1.9
- [ ] **Quick Exchange Mode**: Exchange confirmation button with co-parent notification and history log
- [ ] **One-tap Override Dashboard**: Handle unexpected events (delays, extra sleepover) with one click

### v2.0 (Future Vision 🌟)
- [ ] **Co-parent Mode**: Synchronization between two Home Assistant instances
- [ ] **Financial Management**: Shared expense and alimony tracking
- [ ] **Exchange Journal**: Shared notes and photos during transitions

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. **Fork** the project
2. **Create** a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Development

To develop locally:

```bash
# Clone the repository
git clone https://github.com/Jackngl/custody.git
cd custody

# Install in Home Assistant
cp -r custom_components/custody_schedule /config/custom_components/
```

### CI/CD Workflow

The project uses several automated workflows to ensure quality and maintenance:

#### Automated Tests and Validation

On each push or pull request, the following workflows are executed:

- **Lint & Code Quality**: Formatting check (Black), import sorting (Isort), linting (Flake8), YAML validation
- **Security Scan**: Security analysis with Bandit
- **Unit Tests**: Unit tests with Pytest and coverage report generation
- **Hassfest Validation**: Validation of Home Assistant standards compliance
- **HACS Validation**: HACS compatibility check
- **Core Compatibility Check**: Home Assistant Core compatibility verification

#### Versioning Workflow

The project uses an automated workflow for tag and release creation:

- **Auto-increment**: Every merge to `main` automatically increments the version (patch)
- **Tag Creation**: A Git tag is automatically created for each new version
- **GitHub Releases**: A GitHub release is automatically generated with release notes
- **Badge Update**: The version badge in the README is automatically updated

**Important**: If you make a manual version change or a documentation fix that doesn't require a new release, add **`[skip version]`** in your commit message to disable auto-increment.

#### Promotion to Official Repository

When a release is published, an automated workflow promotes changes to the official repository (`Jackngl/custody`) with fast-forward validation to ensure security.

### Tests

Tests can be performed via the API test service:

```yaml
service: custody_schedule.test_holiday_api
data:
  zone: "A"
```

To run tests locally:

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run tests
pytest tests --cov=custom_components/custody_schedule --cov-report=term-missing
```

---

## 📝 License

MIT © Custody Schedule

---

## 🙏 Acknowledgments

Thanks to:
- The Home Assistant community for their support
- The French Ministry of Education for the school holiday API
- All parents in shared custody who use this integration

---

## 📚 Additional Documentation

For detailed configuration guides, see:

### English
- **[Regular Custody Configuration Guide](README_CONFIG_GARDE.md)** - Configure weekends and alternate weeks
- **[School Holidays Configuration Guide](README_CONFIG_VACANCES.md)** - Configure school holiday rules
- **[Entities Guide](README_ENTITES.md)** - Complete reference of all entities and their usage

### Français
- **[Guide de Configuration - Garde Classique](README_CONFIG_GARDE.fr.md)** - Configurer les weekends et semaines alternées
- **[Guide de Configuration - Vacances Scolaires](README_CONFIG_VACANCES.fr.md)** - Configurer les règles de vacances scolaires
- **[Guide des Entités](README_ENTITES.fr.md)** - Référence complète de toutes les entités et leur utilisation

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Jackngl/custody/issues)
- **Documentation**: This README
- **Logs**: Check Home Assistant logs to diagnose issues

---

<div align="center">

**Made with ❤️ for shared custody families**

</div>
