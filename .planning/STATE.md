# State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-03-11)

**Core value:** Make monthly opportunity-loss calculation easier to operate from the browser without changing the current V5 business logic.
**Current focus:** Scope has been reduced to a stateless/no-storage MVP first; persistence is deferred to a later phase.

## Planning Artifacts

- Codebase map: `.planning/codebase/`
- Research: `.planning/research/`
- Requirements: `.planning/REQUIREMENTS.md`
- Roadmap: `.planning/ROADMAP.md`
- Config: `.planning/config.json`

## Notes

- Brownfield source of truth for calculation logic is `v5_daily_oos_opportunity/`
- Product direction is an internal workflow-first web app
- Current MVP direction is stateless: user uploads required files per run, runs V5, reviews QA, and exports results
- Sales history persistence, duplicate detection, and reusable stored datasets have been intentionally moved to a later enhancement phase
