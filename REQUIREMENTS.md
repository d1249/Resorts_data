# Requirements

## Functional

- Provide a Streamlit app that builds 12-month climate normals for configured locations and displays scores and charts.
- Fetch air temperature/rain, sea temperature, wind, and wave data from public APIs with a file-backed cache.
- Compute ComfortScore and component penalties using parameters stored in YAML.
- Export monthly results to CSV (UTF-8-SIG, semicolon delimiter, decimal comma) and provenance metadata to JSON.
- Allow optional Markdown export for monthly tables.

## Behavioral

- Cache-first fetching with a UI toggle to force refresh.
- Provide penalty decomposition and highlight top contributors to low scores.

## Workflow

- `pip install -r requirements.txt`
- `streamlit run app.py`
