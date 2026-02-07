# Pull Request: Modular System & Weekend Start Day

## Description

This PR implements two major features to improve flexibility and usability:

1.  **Configurable Weekend Start Day (Phase 1)**
    *   Allows users to choose between **Friday** (default) or **Saturday** as the start day for the "Alternate Weekends" custody type.
    *   New field in configuration flow (only visible for this custody type).

2.  **Modular System (Phase 2)**
    *   Introduces a **"Vacations-Only" mode**.
    *   Users can now **enable/disable custody management** via a toggle in the initial setup or the new "Features" options menu.
    *   If custody is disabled:
        *   Configuration flow skips custody and schedule steps.
        *   Vacation step hides irrelevant fields (split mode, parental role).
        *   Schedule generator creates only vacation events (and holidays if configured), no custody weekends/weeks.

## Changes

-   `const.py`: Added `CONF_WEEKEND_START_DAY` and `CONF_ENABLE_CUSTODY`.
-   `config_flow.py`:
    -   Added conditional logic to show/hide steps based on `enable_custody`.
    -   Added "Features" menu in OptionsFlow.
    -   Added weekend start day selector.
-   `schedule.py`:
    -   Updated `alternate_weekend` logic to respect start day config.
    -   Updated generator to return empty list if custody is disabled.
-   `strings.json`: Added translations for new fields and menus.

## Verification

-   [x] **Weekend Start**: Verified Friday vs Saturday start dates in calendar.
-   [x] **Vacations-Only Mode**: Verified flow skips custody steps and generates no custody events.
-   [x] **Full Mode**: Verified standard behavior allows full configuration.
-   [x] **Options Flow**: Verified toggling features updates menu and behavior.
