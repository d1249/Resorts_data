from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.pipeline import build_monthly_table, load_locations, load_params, load_sources
from src.report.plots import (
    METRIC_OPTIONS,
    plot_components_month,
    plot_components_overview,
    plot_metric,
    plot_scores,
)

ROOT = Path(__file__).parent
CONFIG_DIR = ROOT / "config"
OUTPUTS_DIR = ROOT / "outputs"
CACHE_DIR = ROOT / "data" / "cache"

st.set_page_config(page_title="Climate Comfort Score", layout="wide")

st.title("Climate Comfort Score")

locations = load_locations(CONFIG_DIR / "locations.yaml")
params = load_params(CONFIG_DIR / "params.yaml")
sources_cfg = load_sources(CONFIG_DIR / "sources.yaml")

location_map = {loc.location_id: loc for loc in locations}
selected_id = st.selectbox("Location", list(location_map.keys()))
location = location_map[selected_id]

col1, col2 = st.columns(2)
with col1:
    st.write(f"**Country:** {location.country}")
    st.write(f"**Resort:** {location.resort}")
    st.write(f"**Area:** {location.area}")
with col2:
    st.write(f"**Lat/Lon:** {location.lat}, {location.lon}")
    st.write(
        f"**Wave point:** {location.wave_point.lat}, {location.wave_point.lon} ({location.wave_point.mode})"
    )

refresh = st.checkbox("Force refresh", value=False)
export_md = st.checkbox("Export Markdown", value=False)

if st.button("Build / Refresh"):
    with st.spinner("Building monthly climate table..."):
        df, provenance, csv_path, md_path = build_monthly_table(
            location=location,
            sources_cfg=sources_cfg,
            params=params,
            cache_dir=CACHE_DIR,
            outputs_dir=OUTPUTS_DIR,
            refresh=refresh,
            export_md=export_md,
        )

    st.success("Completed!")

    display_df = df.copy()
    display_df = display_df[
        [
            "Country",
            "Resort",
            "Area",
            "Month",
            "AirTempC",
            "SeaTempC",
            "RainDays",
            "Wind_ms",
            "WaveHs_m",
            "ComfortScore",
        ]
    ]

    st.subheader("Monthly table")
    st.dataframe(display_df, use_container_width=True)

    st.subheader("ComfortScore by month")
    plot_scores(df)

    st.subheader("Air/Sea/Rain/Wind/Wave")
    metric_choice = st.selectbox("Metric", list(METRIC_OPTIONS.keys()))
    plot_metric(df, metric_choice)

    st.subheader("Component decomposition by month")
    plot_components_overview(df)

    month_choice = st.selectbox("Decomposition month", df["Month"].tolist())
    plot_components_month(df, int(month_choice))

    month_row = df.loc[df["Month"] == int(month_choice)].iloc[0]
    penalties = {
        "Cold": month_row["Cold"],
        "WindExCold": month_row["WindExCold"],
        "WetPen": month_row["WetPen"],
        "RainPen": month_row["RainPen"],
        "HeatPen": month_row["HeatPen"],
        "BreathPen": month_row["BreathPen"],
        "StrongWindPen": month_row["StrongWindPen"],
        "WavePen": month_row["WavePen"],
    }
    top_penalties = [
        item for item in sorted(penalties.items(), key=lambda item: item[1], reverse=True) if item[1] > 0
    ][:3]
    st.subheader("Почему месяц плохой")
    if top_penalties:
        for name, value in top_penalties:
            st.write(f"- {name}: {value:.1f}")
    else:
        st.write("Штрафов нет — месяц выглядит комфортным.")

    st.subheader("Provenance")
    with st.expander("Подробности источников"):
        st.json(provenance)
    source_summary = {
        "air_rain": provenance["sources"]["air_rain"].get("source"),
        "sea": provenance["sources"]["sea"].get("source"),
        "wind": provenance["sources"]["wind_wave"]["components"]["wind"].get("source"),
        "wave": provenance["sources"]["wind_wave"]["components"]["wave"].get("source"),
    }
    st.write("**Summary:**", source_summary)

    st.download_button(
        label="Download CSV",
        data=csv_path.read_bytes(),
        file_name=csv_path.name,
        mime="text/csv",
    )
    if md_path and md_path.exists():
        st.download_button(
            label="Download Markdown",
            data=md_path.read_bytes(),
            file_name=md_path.name,
            mime="text/markdown",
        )
