from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import json

from season_analytics import render_season_analytics
from driver_comparison import render_driver_comparison
from telemetry_analytics import render_telemetry_analytics
from streaming_monitor import render_streaming_monitor

# Cartella principale
BASE_DIR = Path(__file__).resolve().parents[2]

GOLD_PATH = BASE_DIR / "data/gold/driver_race_performance"

st.set_page_config(
    page_title="F1 Race Intelligence",
    page_icon="🏎️",
    layout="wide"
)

@st.cache_data
def load_data():
    return pd.read_parquet(GOLD_PATH)


st.title("🏎️ F1 Race Intelligence")
st.caption("Formula 1 — Season 2024 | Big Data Analytics")

try:
    df = load_data()
except Exception as exc:
    st.error(f"Errore nel caricamento dei dati: {exc}")
    st.stop()

section = st.sidebar.radio(
    "Navigation",
    [
        "Race Analytics",
        "Season Analytics",
        "Driver Comparison",
        "Telemetry Analytics",
        "Live Streaming Monitor",
    ],
)

if section == "Season Analytics":
    render_season_analytics(df)
    st.stop()

if section == "Driver Comparison":
    render_driver_comparison(df)
    st.stop()

if section == "Telemetry Analytics":
    drivers_path = BASE_DIR / "data/bronze/drivers_2024.json"

    with drivers_path.open(encoding="utf-8") as file:
        drivers_data = json.load(file)

    drivers_df = pd.DataFrame(drivers_data)

    render_telemetry_analytics(df, drivers_df)
    st.stop()

if section == "Live Streaming Monitor":
    render_streaming_monitor()
    st.stop()
    
st.sidebar.header("Race Selection")

# Selezione Gran Premio con session_key
races = (
    df[["session_key", "circuit", "country"]]
    .drop_duplicates()
    .sort_values("circuit")
)

race_options = {
    f"{row.country} — {row.circuit}": row.session_key
    for row in races.itertuples()
}

selected_race = st.sidebar.selectbox(
    "Select Grand Prix",
    options=list(race_options.keys()),
    index=(
        list(race_options.keys()).index("Italy — Monza")
        if "Italy — Monza" in race_options
        else 0
    )
)

session_key = race_options[selected_race]

race_df = df[df["session_key"] == session_key].copy()

race_df = race_df.sort_values(
    "fastest_lap_seconds"
)

st.subheader(selected_race)


col1, col2, col3 = st.columns(3)

col1.metric(
    "Drivers",
    len(race_df)
)

col2.metric(
    "Fastest Lap",
    f"{race_df['fastest_lap_seconds'].min():.3f} s"
)

col3.metric(
    "Valid Laps",
    int(race_df["valid_laps"].sum())
)

st.divider()

# Grafico tempi sul giro
st.subheader("Fastest Laps by Driver")

fig = px.bar(
    race_df,
    x="full_name",
    y="fastest_lap_seconds",
    color="team_name",
    hover_data=[
        "valid_laps",
        "avg_lap_seconds"
    ],
    labels={
        "full_name": "Driver",
        "fastest_lap_seconds": "Fastest Lap (s)",
        "team_name": "Team"
    }
)

fig.update_layout(
    xaxis_tickangle=-45,
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Confronto tempi medi
st.subheader("Average Lap Time Comparison")

fig_avg = px.scatter(
    race_df,
    x="fastest_lap_seconds",
    y="avg_lap_seconds",
    color="team_name",
    hover_name="full_name",
    labels={
        "fastest_lap_seconds": "Fastest Lap (s)",
        "avg_lap_seconds": "Average Lap (s)"
    }
)

st.plotly_chart(fig_avg, use_container_width=True)

# Tabella completa
st.subheader("Driver Performance")

st.dataframe(
    race_df[
        [
            "full_name",
            "team_name",
            "valid_laps",
            "fastest_lap_seconds",
            "avg_lap_seconds",
            "lap_stddev_seconds"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Data source: OpenF1 API | "
    "Processing: Apache Spark | "
    "Storage: Parquet"
)