from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[2]
TELEMETRY_DIR = BASE_DIR / "data/bronze/car_data"

TELEMETRY_GOLD_PATH = (
    BASE_DIR / "data/gold/telemetry_performance_2024_v2"
)


@st.cache_data
def load_telemetry_gold():
    return pd.read_parquet(TELEMETRY_GOLD_PATH)


@st.cache_data(max_entries=3)
def load_telemetry(path, modified_time):
    data = pd.read_json(path)

    data["date"] = pd.to_datetime(
        data["date"], utc=True
    )

    return data.sort_values("date")


def render_telemetry_analytics(races, drivers):
    st.title("Telemetry Analytics")
    st.caption("Formula 1 — 2024 Car Telemetry")

    try:
        telemetry_gold = load_telemetry_gold()
    except Exception as exc:
        st.error(f"Unable to load telemetry Gold: {exc}")
        return

    # Individuo soltanto i file già scaricati
    available_files = sorted(
        TELEMETRY_DIR.glob("*_driver_*.json")
    )

    if not available_files:
        st.warning("No telemetry data available.")
        return

    available = []

    for path in available_files:
        try:
            session, driver = path.stem.split("_driver_")

            available.append({
                "session_key": int(session),
                "driver_number": int(driver),
                "path": path,
            })

        except ValueError:
            continue

    available_df = pd.DataFrame(available)

    # Associazione con i Gran Premi
    race_info = races[
        ["session_key", "country", "circuit"]
    ].drop_duplicates()

    available_df = available_df.merge(
        race_info,
        on="session_key",
        how="left"
    )

    race_options = (
        available_df[
            ["session_key", "country", "circuit"]
        ]
        .drop_duplicates()
        .sort_values("session_key")
    )

    race_labels = {
        f"{row.country} — {row.circuit}": row.session_key
        for row in race_options.itertuples()
    }

    selected_race = st.selectbox(
        "Select Grand Prix",
        list(race_labels.keys())
    )

    session_key = race_labels[selected_race]


    # ======================================
    # GRAND PRIX TELEMETRY COMPARISON — GOLD
    # =====================================

    gp_gold = telemetry_gold[
        telemetry_gold["session_key"] == session_key
    ].copy()

    driver_names = drivers[
        ["session_key", "driver_number", "full_name"]
    ].drop_duplicates(
        subset=["session_key", "driver_number"]
    )

    gp_gold = gp_gold.merge(
        driver_names,
        on=["session_key", "driver_number"],
        how="left"
    )

    gp_gold["driver_label"] = gp_gold.apply(
        lambda row: (
            f"{row['full_name']} (#{row['driver_number']})"
            if pd.notna(row["full_name"])
            else f"Driver #{row['driver_number']}"
        ),
        axis=1
    )

    st.subheader("Grand Prix Telemetry Comparison")

    if gp_gold.empty:
        st.warning("No Gold telemetry available for this Grand Prix.")
    else:
        comparison_metric = st.selectbox(
            "Comparison Metric",
            [
                "Maximum Speed",
                "Average Speed",
                "Maximum RPM",
                "Accelerating Samples (%)",
                "Braking Samples (%)"
            ]
        )

        metric_columns = {
            "Maximum Speed": "max_speed_kmh",
            "Average Speed": "avg_speed_kmh",
            "Maximum RPM": "max_rpm",
            "Accelerating Samples (%)": "accelerating_samples_pct",
            "Braking Samples (%)": "braking_samples_pct"
        }

        selected_column = metric_columns[comparison_metric]

        comparison = gp_gold.sort_values(
            selected_column,
            ascending=False
        )

        fig_comparison = px.bar(
            comparison,
            x="driver_label",
            y=selected_column,
            labels={
                "driver_label": "Driver",
                selected_column: comparison_metric
            },
            hover_data=["total_events"]
        )

        fig_comparison.update_layout(
            xaxis_tickangle=-45
        )

        st.plotly_chart(
            fig_comparison,
            use_container_width=True
        )

        with st.expander("View Grand Prix Telemetry Statistics"):
            st.dataframe(
                comparison[
                    [
                        "driver_label",
                        "total_events",
                        "max_speed_kmh",
                        "avg_speed_kmh",
                        "max_rpm",
                        "accelerating_samples_pct",
                        "braking_samples_pct"
                    ]
                ],
                hide_index=True,
                use_container_width=True
            )

    st.divider()
    st.subheader("Driver Telemetry Detail")


    race_files = available_df[
        available_df["session_key"] == session_key
    ].copy()

    # Associazione piloti
    driver_info = drivers[
        ["session_key", "driver_number", "full_name"]
    ].drop_duplicates()

    race_files = race_files.merge(
        driver_info,
        on=["session_key", "driver_number"],
        how="left"
    )

    race_files["driver_label"] = race_files.apply(
        lambda row: (
            f"{row['full_name']} (#{row['driver_number']})"
            if pd.notna(row["full_name"])
            else f"Driver #{row['driver_number']}"
        ),
        axis=1
    )

    driver_options = {
        row.driver_label: row.path
        for row in race_files.itertuples()
    }

    selected_driver = st.selectbox(
        "Select Driver",
        list(driver_options.keys())
    )

    selected_path = driver_options[selected_driver]

    try:
        telemetry = load_telemetry(
            str(selected_path),
            selected_path.stat().st_mtime
        )

    except Exception as exc:
        st.error(f"Unable to load telemetry: {exc}")
        return

    if telemetry.empty:
        st.warning("Telemetry file is empty.")
        return

    # Tempo relativo dall'inizio della registrazione
    telemetry["elapsed_minutes"] = (
        telemetry["date"] - telemetry["date"].min()
    ).dt.total_seconds() / 60

    # Statistiche principali
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Telemetry Events", f"{len(telemetry):,}")
    c2.metric("Maximum Speed", f"{telemetry['speed'].max():.0f} km/h")
    c3.metric("Average Speed", f"{telemetry['speed'].mean():.1f} km/h")
    c4.metric("Maximum RPM", f"{telemetry['rpm'].max():,.0f}")

    st.divider()

    # Campionamento per rendere i grafici più veloci
    max_points = 5000

    step = max(1, len(telemetry) // max_points)

    chart_data = telemetry.iloc[::step].copy()

    st.subheader("Speed Over Time")

    fig_speed = px.line(
        chart_data,
        x="elapsed_minutes",
        y="speed",
        labels={
            "elapsed_minutes": "Elapsed Time (minutes)",
            "speed": "Speed (km/h)"
        }
    )

    st.plotly_chart(fig_speed, use_container_width=True)

    st.subheader("Engine RPM")

    fig_rpm = px.line(
        chart_data,
        x="elapsed_minutes",
        y="rpm",
        labels={
            "elapsed_minutes": "Elapsed Time (minutes)",
            "rpm": "Engine RPM"
        }
    )

    st.plotly_chart(fig_rpm, use_container_width=True)

    st.subheader("Throttle and Brake")

    fig_controls = px.line(
        chart_data,
        x="elapsed_minutes",
        y=["throttle", "brake"],
        labels={
            "elapsed_minutes": "Elapsed Time (minutes)",
            "value": "Signal Value",
            "variable": "Signal"
        }
    )

    st.plotly_chart(fig_controls, use_container_width=True)

    st.subheader("Gear Selection")

    fig_gear = px.line(
        chart_data,
        x="elapsed_minutes",
        y="n_gear",
        labels={
            "elapsed_minutes": "Elapsed Time (minutes)",
            "n_gear": "Gear"
        }
    )

    st.plotly_chart(fig_gear, use_container_width=True)

    st.subheader("DRS Signal")

    fig_drs = px.line(
        chart_data,
        x="elapsed_minutes",
        y="drs",
        labels={
            "elapsed_minutes": "Elapsed Time (minutes)",
            "drs": "DRS Status Code"
        }
    )

    st.plotly_chart(fig_drs, use_container_width=True)

    st.caption(
        "Source: OpenF1 Car Data API. "
        "Charts display a sampled subset of telemetry points "
        "for performance. KPI values use the complete file. "
        "DRS values are raw status codes."
    )