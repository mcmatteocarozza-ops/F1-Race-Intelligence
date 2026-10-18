import pandas as pd
import plotly.express as px
import streamlit as st


def render_season_analytics(df):
    st.title("Season Analytics")
    st.caption("Formula 1 — 2024 Season Performance")

    season = df.copy()

    season["fastest_lap_seconds"] = pd.to_numeric(
        season["fastest_lap_seconds"],
        errors="coerce"
    )

    season["avg_lap_seconds"] = pd.to_numeric(
        season["avg_lap_seconds"],
        errors="coerce"
    )

    # Miglior giro per ogni Gran Premio
    race_best = (
        season.groupby("session_key")["fastest_lap_seconds"]
        .transform("min")
    )

    # Distacco percentuale dal giro più veloce della gara
    season["gap_percentage"] = (
        (
            season["fastest_lap_seconds"] - race_best
        ) / race_best
    ) * 100

    season = season.dropna(
        subset=["gap_percentage", "full_name"]
    )

    drivers = sorted(season["full_name"].unique())

    selected_driver = st.selectbox(
        "Select Driver",
        drivers
    )

    driver_df = season[
        season["full_name"] == selected_driver
    ].copy()

    driver_df = driver_df.sort_values("session_key")

    # Statistiche generali
    races = driver_df["session_key"].nunique()

    total_laps = int(
        driver_df["valid_laps"].sum()
    )

    avg_gap = driver_df["gap_percentage"].mean()

    best_gap = driver_df["gap_percentage"].min()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Grand Prix", races)
    col2.metric("Valid Laps", total_laps)
    col3.metric("Average Gap", f"{avg_gap:.2f}%")
    col4.metric("Best Gap", f"{best_gap:.2f}%")

    st.divider()

    # Evoluzione delle prestazioni durante la stagione
    st.subheader("Performance Evolution")

    fig = px.line(
        driver_df,
        x="circuit",
        y="gap_percentage",
        markers=True,
        hover_data=[
            "country",
            "fastest_lap_seconds",
            "avg_lap_seconds"
        ],
        labels={
            "circuit": "Grand Prix",
            "gap_percentage": "Gap to Race Fastest Lap (%)"
        }
    )

    fig.update_layout(
        height=450,
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # Classifica stagionale basata su distacco medio
    st.subheader("Season Performance Ranking")

    ranking = (
        season.groupby("full_name", as_index=False)
        .agg(
            grand_prix=("session_key", "nunique"),
            avg_gap_percentage=("gap_percentage", "mean"),
            best_gap_percentage=("gap_percentage", "min")
        )
    )

    ranking = ranking.sort_values(
        "avg_gap_percentage"
    )

    fig_ranking = px.bar(
        ranking,
        x="full_name",
        y="avg_gap_percentage",
        color="avg_gap_percentage",
        labels={
            "full_name": "Driver",
            "avg_gap_percentage": "Average Gap (%)"
        },
        color_continuous_scale="RdYlGn_r"
    )

    fig_ranking.update_layout(
        height=500,
        xaxis_tickangle=-45,
        coloraxis_showscale=False
    )

    st.plotly_chart(
        fig_ranking,
        use_container_width=True
    )

    st.subheader("Season Statistics")

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Ranking based on average percentage gap "
        "to the fastest recorded lap in each race. "
        "Not an official championship classification."
    )