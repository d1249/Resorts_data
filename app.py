from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.formatting import format_with_flag
from src.pipeline import build_monthly_table, load_locations, load_params, load_sources
from src.report.plots import plot_components, plot_metrics, plot_scores

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
        df, provenance, csv_path = build_monthly_table(
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
    display_df["AirTempC_avgHigh"] = [
        format_with_flag(val, flag) for val, flag in zip(df["AirTempC_avgHigh"], df["flag_air"])
    ]
    display_df["SeaTempC"] = [
        format_with_flag(val, flag) for val, flag in zip(df["SeaTempC"], df["flag_sea"])
    ]
    display_df["RainDays_ge1mm"] = [
        format_with_flag(val, flag, decimals=0) for val, flag in zip(df["RainDays_ge1mm"], df["flag_rain"])
    ]
    display_df["Wind_ms_10m"] = [
        format_with_flag(val, flag) for val, flag in zip(df["Wind_ms_10m"], df["flag_wind"])
    ]
    display_df["WaveHeightHs_m"] = [
        format_with_flag(val, flag) for val, flag in zip(df["WaveHeightHs_m"], df["flag_wave"])
    ]

    st.subheader("Monthly table")
    st.dataframe(display_df, use_container_width=True)

    st.subheader("ComfortScore by month")
    plot_scores(df)

    st.subheader("Air/Sea/Rain/Wind/Wave")
    plot_metrics(df)

    month_choice = st.selectbox("Decomposition month", df["Month"].tolist())
    plot_components(df, int(month_choice))

    month_row = df.loc[df["Month"] == int(month_choice)].iloc[0]
    penalties = {
        "WavePen": month_row["WavePen"],
        "RainPen": month_row["RainPen"],
        "WetPen": month_row["WetPen"],
        "HeatPen": month_row["HeatPen"],
        "BreathPen": month_row["BreathPen"],
        "StrongWindPen": month_row["StrongWindPen"],
    }
    top_penalties = sorted(penalties.items(), key=lambda item: item[1], reverse=True)[:3]
    st.write("**Top penalties:**")
    for name, value in top_penalties:
        st.write(f"- {name}: {value:.1f}")

    st.download_button(
        label="Download CSV",
        data=csv_path.read_bytes(),
        file_name=csv_path.name,
        mime="text/csv",
    )
