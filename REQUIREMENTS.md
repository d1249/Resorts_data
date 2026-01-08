# Requirements

## Current Focus
### Streamlit climate comfort pipeline
**Goal:**  
Deliver a no-DB Streamlit app that builds 12-month climate normals, computes ComfortScore with decomposition, and exports results with provenance.

**Scope:**  
- Fetch air/rain, sea temperature, wind, and wave data from public APIs with file-backed cache.
- Aggregate daily data into monthly normals with coverage checks and flags.
- Compute ComfortScore and component penalties using YAML parameters.
- Visualize monthly scores, metrics, and component breakdowns.
- Export CSV (UTF-8-SIG, semicolon delimiter, decimal comma) and provenance JSON; optional Markdown export.

**Non-goals:**  
- Database storage or persistence beyond file cache.
- Authenticated or paid data providers.

**Acceptance Criteria:**
- [ ] Streamlit app runs via `streamlit run app.py` and displays monthly table, charts, and decomposition.
- [ ] CSV export includes required columns and locale formatting.
- [ ] Provenance JSON records sources, period, coordinates, and coverage metrics.

**Edge Cases:**
- [ ] Cache miss with API unavailable falls back to cached or raises a visible error.
- [ ] Months with insufficient coverage are flagged and displayed with `+` indicators.

**Constraints:**
- [ ] File-backed cache in `data/cache/` with TTL configuration.
- [ ] No database usage.

**Notes/Links:**  
- Config files live under `config/`.

## Backlog (Optional)
- Add additional locations and optional provider fallbacks.
