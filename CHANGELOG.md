# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This file was started with the changes below; see the git history for earlier
changes.

## 0.6.5

### Breaking

- Renamed the integration domain from `ksemhst` to `ksemnobr`. Home Assistant
  keys config entries and entities by domain, so existing installations are
  not migrated automatically: remove the integration and add it again via the
  config UI after updating, and update any dashboards/automations that
  reference `ksemhst_*` entity IDs.

### Fixed

- Phase switching (`Phase Switching` select entity) no longer flips back to
  the previous option while the KSEM is still applying a switch. The KSEM can
  take up to 3 minutes to execute a phase switch; the entity previously read
  the current value straight from the coordinator and forced an immediate
  refresh right after writing the new value, which read back the still-stale
  value and reverted the UI. The just-selected value is now shown
  optimistically until the coordinator confirms it or a 200s timeout is
  reached.
