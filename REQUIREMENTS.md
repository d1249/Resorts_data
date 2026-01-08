# Requirements

## Current Focus
### Streamlit climate comfort pipeline (Variant 1: file-based, no DB)
**Goal:**  
Deliver a no-DB Streamlit app that builds 12-month climate normals for preset locations, computes ComfortScore with decomposition, visualizes results, and exports CSV (plus optional Markdown) with provenance.

**Scope:**  
- Fetch air/rain, sea temperature, wind, and wave data from public APIs with file-backed cache.
- Aggregate daily data into monthly normals with coverage checks and flags.
- Compute ComfortScore and component penalties using YAML parameters.
- Visualize monthly scores, metrics, and component breakdowns.
- Export CSV (UTF-8-SIG, semicolon delimiter, decimal comma), provenance JSON, and optional Markdown.

**Non-goals:**  
- Database storage or persistence beyond file cache.
- Authenticated or paid data providers.

**Data & Configuration:**
- `config/locations.yaml` stores locations with fields: `location_id`, `country`, `resort`, `area`, `lat`, `lon`, `wave_point` (`mode`, `lat`, `lon`), plus optional `notes`, `timezone`, `tags`.
- `config/params.yaml` stores scoring thresholds and coefficients (e.g., `dS`, `SeaMax`, `S0..S4`, `RainT1`, `RainT2`, `ColdAirT`, `WindColdT`, `HeatAirT`, `CalmWindT`, `BreathAirT`, `BreathRainT`, `BreathWindT`, `StrongWindT`, `BreezeW0`, `BreezeW1`, `BreezeRamp`, `WaveT1`, `WaveT2`, `WaveT3`) and rounding.
- `config/sources.yaml` stores the normals period, cache TTL, and source priorities/fallback flags (`allow_estimated_rain_days`, `allow_last_resort`).

**Canonical monthly metrics (12 rows, months 1-12):**
- `AirTempC_avgHigh` = mean daily `tmax` (°C, 0.1).
- `SeaTempC` = mean daily SST (°C, 0.1).
- `RainDays_ge1mm` = count of daily precipitation ≥ 1.0mm (integer).
- `Wind_ms_10m` = mean daily wind speed at 10m (m/s, 0.1).
- `WaveHeightHs_m` = mean significant wave height (m, 0.1).

**Quality & Flags:**
- Coverage rule uses `min_coverage` from `config/sources.yaml`. Months below coverage are flagged.
- Flags are stored in separate columns: `flag_air`, `flag_sea`, `flag_rain`, `flag_wind`, `flag_wave`.
- UI may render a `+` next to flagged values, but CSV must store numeric values and explicit flags.

**ComfortScore model:**
- Implement LET formula in code without inline commentary, using parameters from `config/params.yaml`.
- `compute_score(A, S, R, W, WH, params)` returns `(score_0_100, components_dict)`.
- Components include `SeaBase`, `AirAdj`, `BreezeBonus`, `WetPen`, `RainPen`, `HeatPen`, `BreathPen`, `StrongWindPen`, `WavePen`.
- Final score is clamped to 0..100 and rounded per config.

**Exports:**
- `outputs/{location_id}_monthly.csv` with UTF-8-SIG, `;` delimiter, decimal comma.
- Columns include: `Country`, `Resort`, `Area`, `Month`, all metrics, `ComfortScore`, components, flags, and `sources_summary`.
- Optional `outputs/{location_id}_monthly.md` with a human-readable table.
- `outputs/{location_id}_provenance.json` records source names, period, actual coordinates used, coverage metrics, and cache fallback flags.

**UI requirements:**
- Location dropdown from `locations.yaml`.
- Display coordinates and wave point metadata.
- Period selection (driven by config or UI if supported).
- Buttons for Build/Refresh and download CSV (and optional Markdown).
- Monthly table with flagged values, score chart, metrics chart, and decomposition bar chart.
- "Why month is bad" block listing top 3 penalty components for the selected month.

**Cache requirements:**
- Cache-first behavior with disk storage under `data/cache/`.
- Forced refresh should attempt API, and on failure fallback to cached payloads when available.
- Cache key includes source name/version, location, coordinates, time range, and query parameters.

**Reliability & fallbacks:**
- If a source is unavailable, use fallback providers when configured.
- If data is unavailable and fallbacks are not allowed, show a visible error instead of filling values.
- If a source cannot support the requested period, use its available period and record flags in provenance.

**Testing:**
- Unit tests cover unit conversion helpers (mph→m/s, ft→m, K→C).
- Unit tests cover score clamping and at least one compute_score fixture.

**Acceptance Criteria:**
- [ ] Streamlit app runs via `streamlit run app.py` and displays monthly table, charts, and decomposition.
- [ ] Monthly table has 12 rows for each location, with no empty metric cells.
- [ ] ComfortScore uses parameters from YAML and produces components.
- [ ] CSV export matches required columns, locale formatting, and separate flag columns.
- [ ] Provenance JSON records sources, period, coordinates, coverage metrics, and cache fallback indicators.
- [ ] Cache-first is honored, and forced refresh falls back to cached data if the API is unreachable.
- [ ] Optional Markdown export can be downloaded from the UI when enabled.

**Constraints:**
- [ ] File-backed cache in `data/cache/` with TTL configuration.
- [ ] No database usage.

**Notes/Links:**  
- Config files live under `config/`.

## Backlog (Optional)
- Add additional locations and optional provider fallbacks.
