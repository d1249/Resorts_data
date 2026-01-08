# Requirements

## Current Focus
### Streamlit climate comfort pipeline (Variant 1: file-based, no DB)
**Goal:**  
Deliver a no-DB Streamlit app that builds 12-month climate normals for preset locations, computes ComfortScore with full component decomposition, visualizes results, and exports CSV (plus optional Markdown) with provenance.

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
- `config/params.yaml` stores scoring thresholds and coefficients (`dS`, `SeaMax`, `S0..S4`, `RainT1`, `RainT2`, `ColdAirT`, `WindColdT`, `HeatAirT`, `CalmWindT`, `BreathAirT`, `BreathRainT`, `BreathWindT`, `StrongWindT`, `BreezeW0`, `BreezeW1`, `BreezeRamp`, `WaveT1`, `WaveT2`, `WaveT3`) and rounding.
- `config/sources.yaml` stores the normals period, cache TTL, source priorities, and fallback flags (including `allow_estimated_rain_days`, `allow_last_resort`, plus any proxy configuration such as `mm_per_rain_day_proxy`).

**Canonical monthly metrics (12 rows, months 1-12):**
- `AirTempC` = mean daily highs (`tmax`) (°C, 0.1) or proxy from `tavg` with a + mark.
- `SeaTempC` = mean daily SST (°C, 0.1), Kelvin converted via `C = K - 273.15` as needed.
- `RainDays` = count of daily precipitation ≥ 1.0mm (integer), or proxy from totals with + mark.
- `Wind_ms` = mean daily wind speed at 10m (m/s, 0.1), derived from u/v or converted from km/h or mph as needed.
- `WaveHs_m` = mean significant wave height (Hs) (m, 0.1), derived from feet, median, or range midpoint with + mark.

**Quality & Flags:**
- Coverage rule uses `min_coverage` from `config/sources.yaml`. Months below coverage are flagged.
- If preferred data is missing, try fallback sources in order; if still missing, use last-resort estimates when allowed and mark with `+`.
- Flags are stored in separate columns: `mark_air`, `mark_sea`, `mark_rain`, `mark_wind`, `mark_wave`.
- UI may render a `+` next to flagged values, but CSV must store numeric values and explicit flags.

**Dual representation (numeric vs display):**
- Numeric columns are used for computation and plotting: `AirTempC_num`, `SeaTempC_num`, `RainDays_num`, `Wind_ms_num`, `WaveHs_m_num`.
- Display columns are strings with optional `+` prefix and decimal comma: `AirTempC`, `SeaTempC`, `RainDays`, `Wind_ms`, `WaveHs_m`.

**ComfortScore model:**
- Implement LET formula in code without inline commentary, using parameters from `config/params.yaml`.
- `compute_score(A, S, R, W, WH, params)` returns `(score_0_100, components_dict)`.
- Components include `SeaBase`, `AirAdj`, `Breeze`, `WarmForBreeze`, `BreezeBonus`, `Cold`, `WindExCold`, `WetPen`, `RainPen`, `HeatPen`, `BreathPen`, `StrongWindPen`, `WavePen`, and `Score_raw`.
- Final `ComfortScore` is `clamp(Score_raw, 0..100)` and rounded per config.

**Exports:**
- `outputs/{location_id}_{period}_monthly.csv` with UTF-8-SIG, `;` delimiter, decimal comma.
- CSV columns include identity fields, display fields with `+`, numeric fields, score fields, all components, flags, and `sources_summary`. Minimum required:
  - Identity: `Country`, `Resort`, `Area`, `Month`.
  - Display: `AirTempC`, `SeaTempC`, `RainDays`, `Wind_ms`, `WaveHs_m`.
  - Numeric: `AirTempC_num`, `SeaTempC_num`, `RainDays_num`, `Wind_ms_num`, `WaveHs_m_num`.
  - Score: `Score`, `ComfortScore`, `Score_raw`.
  - Components: `SeaBase`, `AirAdj`, `Breeze`, `WarmForBreeze`, `BreezeBonus`, `Cold`, `WindExCold`, `WetPen`, `RainPen`, `HeatPen`, `BreathPen`, `StrongWindPen`, `WavePen`.
  - Marks: `mark_air`, `mark_sea`, `mark_rain`, `mark_wind`, `mark_wave`.
  - Provenance summary: `sources_summary`, plus optional `air_source`, `sea_source`, `wind_source`, `wave_source`.
- Optional `outputs/{location_id}_{period}_monthly.md` with a human-readable table.
- `outputs/{location_id}_{period}_provenance.json` records source names, period requested vs actual, coordinates or station IDs used, coverage metrics, cache fallback flags, and applied `+` marks with reasons.

**UI requirements:**
- Location dropdown from `locations.yaml`.
- Display coordinates and wave point metadata.
- Period selection (driven by config or UI if supported).
- Toggle for force refresh (ignore cache).
- Optional UI controls to override scoring params without refetching.
- Buttons for Build/Refresh and download CSV (and optional Markdown).
- Monthly table with flagged display values, score chart, metrics chart (dropdown for Air/Sea/Rain/Wind/Wave), and decomposition bar chart.
- "Why month is bad" block listing top 3 penalty components for the selected month.
- Provenance panel with readable summary.

**Cache requirements:**
- Cache-first behavior with disk storage under `data/cache/`.
- Forced refresh should attempt API, and on failure fallback to cached payloads when available.
- Cache key includes source name/version, location, coordinates (or station/grid id), time range, variables, and units.

**Reliability & fallbacks:**
- If a source is unavailable, use fallback providers when configured (air/rain should try 2–3 sources, sea 1–2, wind 1 with fallback, wave 1–2).
- If data is unavailable and fallbacks are not allowed, show a visible error instead of filling values.
- If a source cannot support the requested period, use its available period and record flags in provenance.
- Always output 12 months with no blanks when fallbacks are allowed; otherwise fail fast before export.

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
