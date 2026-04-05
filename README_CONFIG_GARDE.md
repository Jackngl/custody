# 📖 Configuration Guide - Regular Custody (Weekends/Weeks)

[🇫🇷 Version française](README_CONFIG_GARDE.fr.md) | [🇬🇧 English version](README_CONFIG_GARDE.md)

This guide explains how to configure **regular custody** (alternate weekends and weeks) in the Custody application.

> ⚠️ **Important**: 
> - This guide concerns **regular custody only** (outside school holidays)
> - **School holidays** are configured separately and have **absolute priority** over regular custody
> - **Public holidays** (Friday/Monday) automatically extend regular custody weekends
> - For school holidays, see the separate holiday rules documentation

---

## 📋 Table of Contents

1. [Separation of regular custody / school holidays](#separation-of-regular-custody--school-holidays)
2. [Available custody types](#available-custody-types)
3. [Basic configuration](#basic-configuration)
4. [Detailed custody types](#detailed-custody-types)
5. [Public holiday management](#public-holiday-management)
6. [Configuration examples](#configuration-examples)

---

## 🎛️ Enable Custody Management

The **"Enable custody management"** option (toggle) allows you to choose between two modes:

### 1. **Enabled (Shared Custody)** - Default
- **Behavior**: The child alternates between parents according to the configured schedule.
- **Status**: Changes between "Present" (at your place) and "Absent" (at the other parent's).
- **Sensors**: `next_arrival` and `next_departure` indicate upcoming exchanges.
- **Vacations**: Divided into halves (or custom rules) to be shared.

### 2. **Disabled (Full Custody)**
- **Behavior**: The child is considered to live primarily with you.
- **Status**: Always **"Present"** (unless manually overridden to "Absent").
- **Sensors**: `next_arrival` and `next_departure` are disabled (no exchanges).
- **Vacations**: **Full vacations** are displayed (no splitting), as the child is with you for the entire holiday.

> **Note**: This setting is available in the initial configuration and in the "Features" menu of the Options.

---


## 🔀 Separation of regular custody / school holidays

The application clearly separates **two independent custody systems**:

### 1. **Regular custody** (this guide)
- **Configuration**: "Regular custody (weekends/weeks)" input form
- **Period**: Outside school holidays only
- **Features**:
  - Alternate weekends, alternate weeks, 2-2-3 patterns, etc.
  - Automatic extension with public holidays (Friday/Monday)
  - Based on cycles or ISO week parity

### 2. **School holidays** (separate documentation)
- **Configuration**: "School holidays" input form
- **Period**: During school holidays only
- **Features**:
  - Rules by half, by week, by year parity
  - Automatic calculation of exact holiday midpoint
  - Absolute priority over regular custody

### ⚠️ Priority Rule

```
School holidays > Public holidays > Regular custody
```

- **During holidays**: Only holiday rules apply
- **Outside holidays**: Regular custody applies, with holiday extension if applicable
- **Public holidays during holidays**: Ignored (holidays already take priority)

---

## 🎯 Available Custody Types

The application supports **6 custody types** for weekends and weeks:

| Type | Code | Description | Cycle | Usage |
|------|------|-------------|-------|-------|
| **Alternate weeks (1/1)** | `alternate_week` | Weekly custody over 2 alternating weeks (14 days) | 14 days | Classic alternating weekly custody (based on reference date) |
| **Alternate weeks** | `alternate_week_parity` | Custody based on ISO week parity (even/odd via reference year) | 7 days | Based on ISO week parity |
| **Alternate weekends** | `alternate_weekend` | Custody based on ISO week parity (even/odd via reference year) | 7 days | Based on ISO week parity |
| **2-2-3** | `two_two_three` | Custody 2 days, break 2 days, custody 3 days | 7 days | Regular weekly pattern |
| **2-2-5-5** | `two_two_five_five` | Custody 2 days, break 2 days, custody 5 days, break 5 days | 14 days | Bi-weekly pattern |
| **Custom** | `custom` | Manually defined custom rules | Variable | Specific cases |

---

## ⚙️ Basic Configuration

### Required Fields

#### 1. **Custody Type** (`custody_type`)
- **Description**: Defines the custody pattern (even weekends, alternating, etc.)
- **Values**: See [Available custody types](#available-custody-types)
- **Example**: `"alternate_weekend"` for even/odd week weekends

#### 2. **My Custody Year (Parity)** (`reference_year_custody`)
- **Description**: Determines whether you have custody on even or odd years (for weekends/weeks).
- **Values**:
  - `"even"`: You have custody during ISO even weeks (2024, 2026, ...).
  - `"odd"`: You have custody during ISO odd weeks (2025, 2027, ...).
- **Note**: In the user interface, these values are displayed as "Even" and "Odd", but the actual configuration value is `"even"` or `"odd"`.
- **Note**: This field calibrates the base alternation. School holidays then automatically alternate each year from this base.

#### 3. **Arrival Time** (`arrival_time`)
- **Description**: Time when you pick up the child
- **Format**: `HH:MM` (e.g., `16:15`)
- **Usage**: Friday after school for weekends
- **Example**: `"16:15"` (primary school dismissal)

#### 4. **Departure Time** (`departure_time`)
- **Description**: Time when you return the child
- **Format**: `HH:MM` (e.g., `19:00`)
- **Usage**: Sunday evening for weekends
- **Example**: `"19:00"` (Sunday evening)

### Optional Fields

#### 5. **Start Day** (`start_day`)
- **Description**: Day marking the start of your custody week (usually Monday).
- **Values**: `"monday"`, `"tuesday"`, `"wednesday"`, `"thursday"`, `"friday"`, `"saturday"`, `"sunday"`
- **Usage**: 
  - ✅ **Used for**: `alternate_week`, `two_two_three`, `two_two_five_five`, `custom`
- ❌ **Not used for**: `alternate_weekend`, `alternate_week_parity` (based on ISO parity via `reference_year_custody`)
- **Default**: `"monday"`
- **Note**: For ISO parity weekends/weeks, the cycle is **always anchored to Monday** (field hidden in interface)

#### 6. **School Level** (`school_level`)
- **Description**: Child's school level (affects dismissal times)
- **Values**:
  - `"primary"`: Primary (dismissal usually 16:15)
  - `"middle"`: Middle school
  - `"high"`: High school
- **Default**: `"primary"`

#### 7. **Exchange Location** (`location`)
- **Description**: Location where custody exchange takes place
- **Format**: Free text
- **Example**: `"Elementary School"`, `"Home"`

#### 8. **Weekend Start Day** (`weekend_start_day`)
- **Description**: Defines the start day for weekend custody.
- **Values**: `"friday"` (default), `"saturday"`
- **Usage**: Only for `alternate_weekend` and `alternate_week_parity`
- **Effect**:
  - `friday`: Weekend starts on Friday (arrival time)
  - `saturday`: Weekend starts on Saturday (arrival time)


---

## 📅 Detailed Custody Types

### 1. Alternate Weekends (`alternate_weekend`)

**How it works**:
- Custody based on **ISO week parity** (even or odd)
- Parity is determined by the `reference_year_custody` field:
  - `reference_year_custody: "even"` → custody on ISO **even** week weekends (S2, S4, S6, S8, ...)
  - `reference_year_custody: "odd"` → custody on ISO **odd** week weekends (S1, S3, S5, S7, ...)
- Based on ISO week number (not a custom cycle)
- **The "Cycle start day" field is not used** (hidden in interface)

**Configuration**:
```yaml
custody_type: "alternate_weekend"
reference_year_custody: "even"  # "even" = even week weekends, "odd" = odd week weekends
arrival_time: "16:15"  # Friday school dismissal
departure_time: "19:00"  # Sunday evening
# start_day is not used for this type
```

**Example** (`reference_year_custody: "even"` = even week weekends):
- ISO Week 18 (even) → ✅ Custody
- ISO Week 19 (odd) → ❌ No custody
- ISO Week 20 (even) → ✅ Custody

**Sample Calendar (May 2025, `reference_year_custody: "even"`)**:
- ✅ S18: Fri 02/05 16:15 → Sun 04/05 19:00
- ❌ S19: No custody
- ✅ S20: Fri 16/05 16:15 → Sun 18/05 19:00
- ❌ S21: No custody
- ✅ S22: Fri 30/05 16:15 → Sun 01/06 19:00

---

### 2. Alternate Weeks (`alternate_week`)

**How it works**:
- Custody **one full week out of two** (14-day cycle)
- Cycle: 7 days "on" + 7 days "off"
- Uses the `start_day` field to determine start day

**Configuration**:
```yaml
custody_type: "alternate_week"
reference_year_custody: "even"
start_day: "monday"  # Start of custody week
arrival_time: "08:00"
departure_time: "19:00"
```

**Example cycle**:
- Week 1: ✅ Mon 08:00 → Sun 19:00 (7 days)
- Week 2: ❌ No custody
- Week 3: ✅ Mon 08:00 → Sun 19:00 (7 days)

---

### 3. Alternate Weeks (`alternate_week_parity`)

**How it works**:
- Custody based on **ISO week parity** (even or odd)
- Parity is determined by the `reference_year_custody` field:
  - `reference_year_custody: "even"` → custody on ISO **even** weeks
  - `reference_year_custody: "odd"` → custody on ISO **odd** weeks
- Cycle: 7 days (one full week)
- **Does not require** the `start_day` field (based on ISO parity)

**Configuration**:
```yaml
custody_type: "alternate_week_parity"
reference_year_custody: "even"  # "even" = even weeks, "odd" = odd weeks
arrival_time: "08:00"
departure_time: "19:00"
```

**Example cycle** (`reference_year_custody: "even"` = even weeks):
- ISO Week 2: ✅ Mon 08:00 → Sun 19:00 (7 days)
- ISO Week 3: ❌ No custody
- ISO Week 4: ✅ Mon 08:00 → Sun 19:00 (7 days)
- ISO Week 5: ❌ No custody

**Difference from `alternate_week`**:
- `alternate_week`: Based on a reference date and a 14-day cycle (1 week out of 2)
- `alternate_week_parity`: Based on ISO week parity (all even or odd weeks according to `reference_year_custody`)

---

### 4. 2-2-3 Pattern (`two_two_three`)

**How it works**:
- Custody **2 days**, break **2 days**, custody **3 days** (7-day cycle)
- Pattern repeated each week
- Uses the `start_day` field to determine cycle start day

**Configuration**:
```yaml
custody_type: "two_two_three"
reference_year_custody: "even"
start_day: "monday"  # Cycle start day
arrival_time: "08:00"
departure_time: "19:00"
```

**Example cycle (7 days)**:
- Days 1-2: ✅ Custody (e.g., Mon-Tue)
- Days 3-4: ❌ No custody (e.g., Wed-Thu)
- Days 5-7: ✅ Custody (e.g., Fri-Sun)
- Then cycle repeats

**Sample Calendar**:
```
Week 1:
  ✅ Mon 08:00 → Tue 19:00 (2 days)
  ❌ Wed-Thu (no custody)
  ✅ Fri 08:00 → Sun 19:00 (3 days)

Week 2:
  ✅ Mon 08:00 → Tue 19:00 (2 days)
  ❌ Wed-Thu (no custody)
  ✅ Fri 08:00 → Sun 19:00 (3 days)
```

---

### 5. 2-2-5-5 Pattern (`two_two_five_five`)

**How it works**:
- Custody **2 days**, break **2 days**, custody **5 days**, break **5 days** (14-day cycle)
- Pattern repeated every 2 weeks
- Uses the `start_day` field to determine cycle start day

**Configuration**:
```yaml
custody_type: "two_two_five_five"
reference_year_custody: "even"
start_day: "monday"  # Cycle start day
arrival_time: "08:00"
departure_time: "19:00"
```

**Example cycle (14 days)**:
- Days 1-2: ✅ Custody (e.g., Mon-Tue)
- Days 3-4: ❌ No custody (e.g., Wed-Thu)
- Days 5-9: ✅ Custody (e.g., Fri-Following Tue)
- Days 10-14: ❌ No custody
- Then cycle repeats

**Sample Calendar**:
```
Week 1:
  ✅ Mon 08:00 → Tue 19:00 (2 days)
  ❌ Wed-Thu (no custody)
  ✅ Fri 08:00 → Following Tue 19:00 (5 days)

Week 2:
  ❌ Wed-Sun (no custody, 5 days)

Week 3:
  ✅ Mon 08:00 → Tue 19:00 (2 days)
  ❌ Wed-Thu (no custody)
  ✅ Fri 08:00 → Following Tue 19:00 (5 days)
  ...
```

---

### 6. Custom (`custom`)

**How it works**:
- Custody rules defined manually via exceptions or custom rules
- Allows creating specific patterns not covered by standard types
- Requires manual period configuration

**Configuration**:
```yaml
custody_type: "custom"
# Periods are defined via custom rules in options
```

**Usage**:
- Access integration options
- Use custom rules to define your periods
- Or use the `set_manual_dates` service to define specific periods

---

## 🎉 Public Holiday Management

The application **automatically extends** custody weekends and weeks when a public holiday falls on a Friday or Monday.

> ⚠️ **Important**: Public holiday extensions **do NOT apply** if the weekend or week falls during a **school holiday period**. School holidays have absolute priority and use their own logic.

### Extension Rules

| Situation | Normal Custody | Custody with Holiday |
|-----------|---------------|---------------------|
| **Monday holiday** | Fri 16:15 → Sun 19:00 | Fri 16:15 → **Mon 19:00** |
| **Friday holiday** | Fri 16:15 → Sun 19:00 | **Thu 16:15** → Sun 19:00 |
| **Bridge (both)** | Fri 16:15 → Sun 19:00 | **Thu 16:15 → Mon 19:00** |

**How it is calculated:** For **alternate weekends** and **alternate weeks (parity)**, the integration uses your country’s built-in public holiday set (France: fixed dates plus Easter Monday, Ascension, Pentecost Monday, and optional Alsace–Moselle days). If the **calendar day after** your configured end day (often Sunday) is a public holiday—e.g. Easter Monday when Sunday is not in the legal list—custody is extended through that day at **departure time**. If the **first day** of the weekend (Friday or Saturday, per your setting) is a public holiday, the start moves **one day earlier** at each step (e.g. Labour Day Friday → Thursday pickup at **arrival time**) until the start day is not a holiday.

### Examples

**Example 1: Easter Monday (April 21, 2025)**
```
Weekend S16 (even week):
- Normal: Fri 18/04 16:15 → Sun 20/04 19:00
- With holiday: Fri 18/04 16:15 → Mon 21/04 19:00 ✅
```

**Example 2: Friday August 15 (Assumption)**
```
Weekend S33 (even week):
- Normal: Fri 15/08 16:15 → Sun 17/08 19:00
- With holiday: Thu 14/08 16:15 → Sun 17/08 19:00 ✅
```

**Example 3: Bridge (Friday + Monday holidays)**
```
Weekend with bridge:
- Normal: Fri 16:15 → Sun 19:00
- With bridge: Thu 16:15 → Mon 19:00 ✅ (4 days of custody)
```

### Calendar Labels

Custody events automatically display extensions:
- `Custody - Even week weekends + Monday holiday`
- `Custody - Even week weekends + Friday holiday`
- `Custody - Even week weekends + Bridge`
- `Custody - Alternate weeks - even weeks + Monday holiday`
- `Custody - Alternate weeks - even weeks + Friday holiday`

---

## 📊 Custody Types Summary Table

| Type | Cycle | Uses start_day | Uses reference_year_custody | Public Holidays |
|------|-------|----------------|----------------------------|-----------------|
| `alternate_week` | 14 days | ✅ Yes | ✅ Yes | ❌ No |
| `alternate_week_parity` | 7 days | ❌ No | ✅ Yes (determines parity) | ✅ Yes |
| `alternate_weekend` | 7 days | ❌ No | ✅ Yes (determines parity) | ✅ Yes |
| `two_two_three` | 7 days | ✅ Yes | ✅ Yes | ❌ No |
| `two_two_five_five` | 14 days | ✅ Yes | ✅ Yes | ❌ No |
| `custom` | Variable | ✅ Yes | ✅ Yes | ❌ No |

**Note**: Custody types based on ISO parity (`alternate_weekend`, `alternate_week_parity`) use `reference_year_custody` to determine parity (even/odd) and benefit from automatic extension with public holidays, **only outside school holidays**.

---

## 📝 Configuration Examples

### Example 1: Even Weekends (Recommended Configuration)

**Situation**: You have custody every even week weekend.

```yaml
# Configuration
custody_type: "alternate_weekend"
reference_year_custody: "even"
arrival_time: "16:15"      # Friday school dismissal
departure_time: "19:00"    # Sunday evening
school_level: "primary"
location: "Elementary School"

# Result (May 2025)
# ✅ S18: Fri 02/05 16:15 → Sun 04/05 19:00
# ❌ S19: No custody
# ✅ S20: Fri 16/05 16:15 → Sun 18/05 19:00
# ❌ S21: No custody
# ✅ S22: Fri 30/05 16:15 → Sun 01/06 19:00
```

### Example 2: Alternate Weeks

**Situation**: Custody one full week out of two, starting Monday.

```yaml
# Configuration
custody_type: "alternate_week"
reference_year_custody: "even"
start_day: "monday"
arrival_time: "08:00"      # Monday morning
departure_time: "19:00"    # Sunday evening
school_level: "primary"

# Result (14-day cycle)
# Week 1: ✅ Mon 08:00 → Sun 19:00 (7 days)
# Week 2: ❌ No custody
# Week 3: ✅ Mon 08:00 → Sun 19:00 (7 days)
```

### Example 3: 2-2-3 Pattern

**Situation**: Custody 2 days, break 2 days, custody 3 days, weekly cycle.

```yaml
# Configuration
custody_type: "two_two_three"
reference_year_custody: "even"
start_day: "monday"
arrival_time: "08:00"
departure_time: "19:00"
school_level: "primary"

# Result (7-day cycle, repeated each week)
# Week 1:
#   ✅ Mon 08:00 → Tue 19:00 (2 days)
#   ❌ Wed-Thu (no custody)
#   ✅ Fri 08:00 → Sun 19:00 (3 days)
# Week 2: Same pattern
```

### Example 4: 2-2-5-5 Pattern

**Situation**: Custody 2 days, break 2 days, custody 5 days, break 5 days, bi-weekly cycle.

```yaml
# Configuration
custody_type: "two_two_five_five"
reference_year_custody: "even"
start_day: "monday"
arrival_time: "08:00"
departure_time: "19:00"
school_level: "primary"

# Result (14-day cycle)
# Week 1:
#   ✅ Mon 08:00 → Tue 19:00 (2 days)
#   ❌ Wed-Thu (no custody)
#   ✅ Fri 08:00 → Following Tue 19:00 (5 days)
# Week 2:
#   ❌ Wed-Sun (no custody, 5 days)
# Then cycle repeats
```

---

## ⚠️ Important Notes

### Configuration Separation

The application uses **two distinct input forms**:

1. **"Regular Custody" Form**:
   - Custody type (alternate_week, alternate_weekend, etc.)
   - Reference year
   - Arrival/departure times
   - Cycle start day
   - School level
   - Exchange location
   - **+ Automatic extension with public holidays**

2. **"School Holidays" Form**:
   - School zone or Subdivision (A/B/C, Cantons, etc.)
   - Half distribution
   - **Summer split**: choose between "2 Halves" (July/August) or "4 Fortnights" (alternating every 15 days).
   - **Fair calculation**: summer is divided into equal parts based on actual holiday dates.

### Rule Priority

1. **School holidays** (absolute priority)
   - During holidays, regular custody rules are **completely ignored**
   - Public holidays during holidays are also ignored
   - Only holiday rules apply
   - **Configured in the "School Holidays" form**

2. **Public holidays** (weekend extension)
   - Apply only to regular custody weekends
   - Have no effect during school holidays
   - **Automatically managed** in regular custody

3. **Regular custody** (weekends/weeks)
   - Applies only outside school holidays
   - Respects public holidays for extension
   - **Configured in the "Regular Custody" form**

### "Cycle Start Day" Field

- ✅ **Used for**: 
  - `alternate_week` (alternate weeks)
  - `two_two_three` (2-2-3 pattern)
  - `two_two_five_five` (2-2-5-5 pattern)
  - `custom` (custom)
- ❌ **Not used for**: `alternate_weekend`, `alternate_week_parity`
  - These types use ISO week parity
  - Field is hidden in interface for these types

### Time Format

- **Expected format**: `HH:MM` (e.g., `16:15`, `19:00`)
- **Accepted format**: `HH:MM:SS` (seconds are ignored)
- **Validation**: Hours 00-23, Minutes 00-59

---

## 🔍 Configuration Verification

### How to verify your configuration is correct?

1. **Check generated weekends**:
   - Go to Home Assistant calendar
   - Custody events should appear on correct weekends
   - Labels should indicate holiday extensions if applicable

2. **Check attributes**:
   - `next_arrival`: Next custody date/time
   - `next_departure`: Next custody end date/time
   - `custody_type`: Configured custody type

3. **Test with a public holiday**:
   - Verify that a weekend with Monday holiday extends to Monday
   - Verify that a weekend with Friday holiday starts on Thursday

---

## 📞 Support

For any questions about regular custody configuration:
- Consult the complete documentation in the main README
- Check Home Assistant logs for errors
- Holiday rules are documented separately

---

**Last updated**: Version 1.8.x (aligned with Custody integration)
