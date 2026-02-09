# 📊 Entities Guide - Custody

[🇫🇷 Version française](README_ENTITES.fr.md) | [🇬🇧 English version](README_ENTITES.md)

This guide explains all entities created by the **Custody** integration and how to use them in your Home Assistant dashboards and automations.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Available Entities](#available-entities)
3. [Dashboard Usage](#dashboard-usage)
4. [Automation Examples](#automation-examples)
5. [Available Attributes](#available-attributes)

---

## 🎯 Overview

The **Custody** integration automatically creates several entities for each configured child:

- **1 Binary Sensor**: Presence status
- **1 Calendar**: Complete calendar
- **1 Device Tracker**: Presence tracking (usable in Person entity)
- **9 Sensors**: Detailed information about custody and holidays

All entities are prefixed by the **child's name slug**: lowercase, spaces replaced by underscores (e.g., "Sarah-Léa" → `sarah_lea`). Replace `{child}` in examples with this slug.

---

## 📦 Available Entities

### 1. Binary Sensor: Presence

**Entity Name**: `binary_sensor.{child}_presence`  
**Display Name**: `{Child} Presence`

#### Description
Indicates whether the child is currently in custody (regular custody or school holidays).

#### States
- **`on`**: Child is currently in custody
- **`off`**: Child is not currently in custody
- **`unavailable`**: Data unavailable

#### Available Attributes
- `child_name`: Child's name
- `custody_type`: Configured regular custody type
- `next_arrival`: Next arrival (ISO format)
- `next_departure`: Next departure (ISO format)
- `vacation_name`: Current holiday name (if applicable)
- `next_vacation_name`: Next holiday name
- `next_vacation_start`: Next holiday start (ISO format)
- `next_vacation_end`: Next holiday end (ISO format)
- `days_until_vacation`: Days until next holidays
- `school_holidays_raw`: Complete list of school holidays

#### 🏠 Behavior in Full Custody Mode
If **custody management is disabled**:
- `custody_type`: Becomes `None`.
- `next_arrival`: Becomes `None` (forced).
- `next_departure`: Becomes `None` (forced).
- `vacation_name`: Displays the full vacation period without splitting.
- **Sensors**: The corresponding sensors will show `unknown` or `None`.


#### Usage
- **Dashboard**: Display visual presence indicator
- **Automation**: Trigger actions when child arrives/leaves

---

### 2. Calendar: Complete Calendar

**Entity Name**: `calendar.{child}_calendar`  
**Display Name**: `{Child} Calendar`

#### Description
Complete calendar displaying all custody events (weekends/weeks and school holidays).

#### Features
- Displays all regular custody events (weekends, weeks)
- Displays all school holiday events
- Visual distinction between regular custody and school holidays
- Compatible with Home Assistant calendar views

#### Event Types
1. **Regular Custody**: Weekends and regular custody weeks
2. **School Holidays**: Holiday periods (Christmas, Winter, Spring, All Saints' Day, Summer)

#### Usage
- **Dashboard**: Integrate into a calendar card
- **Automation**: Use events to trigger actions
- **Calendar View**: Visualize complete schedule

---

### 3. Device Tracker: Presence Tracking

**Entity Name**: `device_tracker.{child}_tracker`  
**Display Name**: `{Child} Tracker`

#### Description
Tracking device based on child presence (regular custody or school holidays). This entity can be used in Home Assistant's **Person** entity to create complete presence tracking.

#### States
- **`home`**: Child is currently in custody (present)
- **`not_home`**: Child is not currently in custody (absent)
- **`unavailable`**: Data unavailable

#### Available Attributes
- `child_name`: Child's name
- `source`: Tracking source (`custody_schedule`)
- `is_present`: Presence state (boolean)

#### Usage
- **Home Assistant Person**: Associate this device tracker with a person for presence tracking
- **Dashboard**: Display presence status in person cards
- **Automation**: Trigger actions based on presence/absence
- **Zones**: Compatible with Home Assistant zone system

#### Person Configuration
1. Go to **Settings** → **People & Zones**
2. Click **Create Person**
3. Name the person (e.g., "Sarah-Léa")
4. In **Device Trackers**, select `device_tracker.{child}_tracker`
5. Add a photo if desired
6. Save

#### Advantages
- ✅ Native integration with Home Assistant Person system
- ✅ Automatic update every 15 minutes
- ✅ Status change history
- ✅ Usable in automations and dashboards
- ✅ Compatible with custom zones

---

### 4. Sensor: Next Arrival

**Entity Name**: `sensor.{child}_next_arrival`  
**Display Name**: `{Child} Next Arrival`

#### Description
Date and time of child's next arrival (regular custody or holidays).

#### Format
- **State**: Timestamp object (Home Assistant automatically handles display based on your language)
- **Class**: `timestamp`

#### Usage
- **Dashboard**: Display next appointment
- **Automation**: Trigger actions before arrival

---

### 5. Sensor: Next Departure

**Entity Name**: `sensor.{child}_next_departure`  
**Display Name**: `{Child} Next Departure`

#### Description
Date and time of child's next departure (regular custody or holidays).

#### Format
- **State**: Timestamp object (automatic display)
- **Class**: `timestamp`

#### Usage
- **Dashboard**: Display next departure
- **Automation**: Trigger actions before departure

---

### 6. Sensor: Days Remaining

**Entity Name**: `sensor.{child}_days_remaining`  
**Display Name**: `{Child} Days Remaining`

#### Description
Number of days remaining before next custody change.

#### Format
- **State**: Decimal number (e.g., `3.5`)
- **Unit**: `d` (displayed as "days")
- **Type**: `duration` (duration)

#### Usage
- **Dashboard**: Display day counter
- **Automation**: Trigger actions based on number of days remaining

---

### 7. Sensor: Current Period

**Entity Name**: `sensor.{child}_current_period`  
**Display Name**: `{Child} Current Period`

#### Description
Current period (regular custody, school holidays, or none).

#### Possible States (Raw Entity Values)
- `"school"`: Non-holiday period (regular custody: weekends/weeks)
- `"vacation"`: School holiday period
- `None` or empty: No custody period in progress (rare case)

#### Usage
- **Dashboard**: Display current period type
- **Automation**: Adapt behavior based on period type

---

### 8. Sensor: Next Holidays

**Entity Name**: `sensor.{child}_next_vacation_name`  
**Display Name**: `{Child} Next Holidays`

#### Description
Name of upcoming school holidays.

#### Possible States
- Values returned by school holiday API (e.g., `"Vacances de Noël"`, `"Vacances d'Hiver"`, `"Vacances de Printemps"`, `"Vacances de la Toussaint"`, `"Vacances d'Été"`).
- `unknown` or empty: No upcoming holiday scheduled or zone not configured.

#### Usage
- **Dashboard**: Display next holiday name
- **Automation**: Adapt behavior based on holiday type

---

### 9. Sensor: Next Holiday Start Date

**Entity Name**: `sensor.{child}_next_vacation_start`  
**Display Name**: `{Child} Next Holiday Start Date`

#### Description
Date and time of next school holiday start.

#### Format
- **State**: Timestamp object (automatic display)
- **Class**: `timestamp`

#### Usage
- **Dashboard**: Display next holiday start date
- **Automation**: Schedule actions before holiday start

---

### 10. Sensor: Days Until Holidays

**Entity Name**: `sensor.{child}_days_until_vacation`  
**Display Name**: `{Child} Days Until Holidays`

#### Description
Number of days remaining before next school holiday start.

#### Format
- **State**: Decimal number (e.g., `15.5`)
- **Unit**: `d`
- **Type**: `duration` (duration)

#### Usage
- **Dashboard**: Display day counter before holidays
- **Automation**: Trigger actions before holidays


### 11. Sensor: Next Change

**Entity Name**: `sensor.{child}_next_change`  
**Display Name**: `{Child} Next Change`

#### Description
Combined sensor summarizing the next event (arrival or departure).

#### Format
- **State**: String (e.g., "16:15" if today, or "Friday 21/02")
- **Icon**: `mdi:calendar-sync`

---

### 12. Sensor: Custody Location

**Entity Name**: `sensor.{child}_parent_in_charge`  
**Display Name**: `{Child} Custody Location`

#### Description
Explicit state indicating where the child is.

#### States
- **`home`**: With me (Present)
- **`away`**: Other parent (Absent)

#### Icon
Dynamic: `mdi:home-account` when present, `mdi:account-arrow-right` when absent.

---

## 🎨 Dashboard Usage

### Example 0: Person Card with Device Tracker

```yaml
type: person
entity: person.sarah_lea
```

This card automatically displays:
- Presence status (home/not_home)
- Person's photo
- Status change history
- Compatible with custom zones

---

### Example 1: Simple Presence Card

```yaml
type: entities
title: Custody - {Child}
entities:
  - entity: binary_sensor.{child}_presence
    name: Presence
    icon: mdi:account-check
  - entity: sensor.{child}_current_period
    name: Current Period
  - entity: sensor.{child}_days_remaining
    name: Days Remaining
```

### Example 2: Card with Next Dates

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Next Dates
    entities:
      - entity: sensor.{child}_next_arrival
        name: Next Arrival
        icon: mdi:calendar-clock
      - entity: sensor.{child}_next_departure
        name: Next Departure
        icon: mdi:calendar-arrow-right
  - type: entities
    title: School Holidays
    entities:
      - entity: sensor.{child}_next_vacation_name
        name: Next Holidays
        icon: mdi:calendar-star
      - entity: sensor.{child}_days_until_vacation
        name: Days Until Holidays
        icon: mdi:calendar-clock
```

### Example 3: Calendar Card

```yaml
type: calendar
entities:
  - entity: calendar.{child}_calendar
title: Custody - {Child}
```

### Example 3 bis: Calendar Card (Monthly View)

```yaml
type: calendar
entities:
  - entity: calendar.{child}_calendar
title: Custody - {Child}
initial_view: dayGridMonth
```

### Example 4: Custom Card with Badges

```yaml
type: custom:mushroom-entity-card
entity: binary_sensor.{child}_presence
name: Presence
icon: mdi:account-check
secondary_info: last-updated
tap_action:
  action: navigate
  navigation_path: /lovelace/planning
```

---

## 🤖 Automation Examples

### Automation 1: Notification Before Arrival

```yaml
alias: "Notification Before Arrival {Child}"
description: "Sends notification 1 hour before child arrival"
trigger:
  - platform: template
    value_template: >
      {% set next_arrival = states('sensor.{child}_next_arrival') %}
      {% if next_arrival != 'unknown' and next_arrival != '' %}
        {{ (as_timestamp(next_arrival) - as_timestamp(now()) <= 3600) and
           (as_timestamp(next_arrival) - as_timestamp(now()) > 0) }}
      {% else %}
        false
      {% endif %}
condition:
  - condition: state
    entity_id: binary_sensor.{child}_presence
    state: 'off'
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "{Child} Arrival"
      message: "{{ states('sensor.{child}_next_arrival') }}"
      data:
        actions:
          - action: "URI"
            title: "View Schedule"
            uri: "/lovelace/planning"
```

### Automation 2: Automatic Heating Before Arrival

```yaml
alias: "Heating Before Arrival {Child}"
description: "Activates heating 2 hours before arrival"
trigger:
  - platform: template
    value_template: >
      {% set next_arrival = states('sensor.{child}_next_arrival') %}
      {% if next_arrival != 'unknown' and next_arrival != '' %}
        {{ (as_timestamp(next_arrival) - as_timestamp(now()) <= 7200) and
           (as_timestamp(next_arrival) - as_timestamp(now()) > 0) }}
      {% else %}
        false
      {% endif %}
condition:
  - condition: state
    entity_id: binary_sensor.{child}_presence
    state: 'off'
action:
  - service: climate.set_temperature
    target:
      entity_id: climate.living_room
    data:
      temperature: 20
```

### Automation 3: Automatic Lighting During Custody

```yaml
alias: "Lighting During Custody {Child}"
description: "Turns on lights when child is in custody in the evening"
trigger:
  - platform: state
    entity_id: binary_sensor.{child}_presence
    to: 'on'
condition:
  - condition: time
    after: '18:00:00'
    before: '23:00:00'
action:
  - service: light.turn_on
    target:
      entity_id: light.child_room
    data:
      brightness: 100
```

### Automation 4: Notification Before Holidays

```yaml
alias: "Notification Before Holidays {Child}"
description: "Notifies 7 days before holiday start"
trigger:
  - platform: template
    value_template: >
      {% set days_until = states('sensor.{child}_days_until_vacation') | float(0) %}
      {{ days_until <= 7 and days_until > 6 }}
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Holidays Approaching!"
      message: >
        The {{ states('sensor.{child}_next_vacation_name') }} 
        start in {{ states('sensor.{child}_days_until_vacation') }} days
```

### Automation 5: Automatic "Holiday" Mode

```yaml
alias: "Holiday Mode {Child}"
description: "Activates special mode during school holidays"
trigger:
  - platform: state
    entity_id: sensor.{child}_current_period
    to: 'vacation'
action:
  - service: input_select.select_option
    target:
      entity_id: input_select.house_mode
    data:
      option: "Holidays"
  - service: notify.mobile_app_your_phone
    data:
      title: "School Holidays"
      message: "Holiday mode activated for {{ states('sensor.{child}_next_vacation_name') }}"
```

### Automation 6: Days Remaining Counter

```yaml
alias: "End of Custody Alert {Child}"
description: "Notifies when less than 1 day of custody remains"
trigger:
  - platform: template
    value_template: >
      {% set days_remaining = states('sensor.{child}_days_remaining') | float(0) %}
      {{ days_remaining <= 1 and days_remaining > 0 }}
condition:
  - condition: state
    entity_id: binary_sensor.{child}_presence
    state: 'on'
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "End of Custody Approaching"
      message: >
        {{ states('sensor.{child}_days_remaining') }} day(s) 
        remaining before next departure
```

---

## 📝 Available Attributes

All entities share common attributes accessible via `{{ state_attr('entity_id', 'attribute_name') }}`:

### Base Attributes
- `child_name`: Child's name
- `custody_type`: Regular custody type (e.g., `alternate_week`, `alternate_weekend`)
- `current_period`: Current period — raw values: `school` (outside holidays), `vacation` (school holidays), or empty

### Date Attributes
- `next_arrival`: Next arrival (ISO format)
- `next_departure`: Next departure (ISO format)
- `days_remaining`: Days remaining before change

### Holiday Attributes
- `vacation_name`: Current holiday name
- `next_vacation_name`: Next holiday name
- `next_vacation_start`: Next holiday start (ISO format)
- `next_vacation_end`: Next holiday end (ISO format)
- `days_until_vacation`: Days until next holidays
- `school_holidays_raw`: Complete holiday list (JSON format)

### Configuration Attributes
- `location`: Exchange location (if configured)
- `notes`: Custom notes (if configured)
- `zone`: School zone or Subdivision (A, B, C, Cantons, etc.)

---

## 💡 Usage Tips

### For Dashboards
1. **Use conditional cards** to display different information based on period
2. **Combine multiple entities** in a single card for an overview
3. **Use icons** to make cards more visual
4. **Create separate views** for regular custody and school holidays

### For Automations
1. **Always check the state** of `binary_sensor.{child}_presence` before acting
2. **Use templates** to calculate delays before events
3. **Test with test values** before going to production
4. **Add conditions** to avoid multiple triggers

### Best Practices
- **Name clearly** your automations with the child's name
- **Document** your custom automations
- **Test regularly** that entities are up to date
- **Use attributes** to get more information than state alone

---

## 🔧 Troubleshooting

### Entities Don't Update
1. Verify that the integration is properly configured
2. Restart Home Assistant
3. Check logs for errors

### Dates Are Incorrect
1. Check school zone configuration
2. Verify that `reference_year_custody` (regular custody) and holiday distribution are correctly configured
3. Check arrival/departure times

### Holidays Don't Display
1. Verify that the school zone is correct
2. Check connection to school holiday API
3. Check logs for API errors

---

## 📚 Additional Resources

- **Regular custody documentation**: `README_CONFIG_GARDE.md`
- **School holiday documentation**: `README_CONFIG_VACANCES.md`
- **Main documentation**: `README.md`

---

## ✅ Entity Summary

| Type | Entity ID | Display Name | Description |
|------|-----------|--------------|-------------|
| Binary Sensor | `binary_sensor.{child}_presence` | {Child} Presence | Presence status |
| Calendar | `calendar.{child}_calendar` | {Child} Calendar | Complete calendar |
| Device Tracker | `device_tracker.{child}_tracker` | {Child} Tracker | Presence (home/not_home) |
| Sensor | `sensor.{child}_next_arrival` | {Child} Next Arrival | Arrival date/time |
| Sensor | `sensor.{child}_next_departure` | {Child} Next Departure | Departure date/time |
| Sensor | `sensor.{child}_days_remaining` | {Child} Days Remaining | Days before change |
| Sensor | `sensor.{child}_current_period` | {Child} Current Period | `school` / `vacation` |
| Sensor | `sensor.{child}_next_vacation_name` | {Child} Next Holidays | Holiday name |
| Sensor | `sensor.{child}_next_vacation_start` | {Child} Vacations Start | Start date |
| Sensor | `sensor.{child}_days_until_vacation` | {Child} Days Until Holidays | Days before holidays |
| Sensor | `sensor.{child}_next_change` | {Child} Next Change | Combined next event |
| Sensor | `sensor.{child}_parent_in_charge` | {Child} Custody Location | home / away |

---

**Note**: Replace `{child}` with the child's name slug (lowercase, spaces → underscores, e.g., `lucas`, `sarah_lea`).
