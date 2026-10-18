import pandas as pd
import plotly.express as px
import streamlit as st


def render_driver_comparison(df):
    st.title("Driver Comparison")
    st.caption("Formula 1 — 2024 Head-to-Head Analysis")

    data = df.copy()

    for column in [
        "fastest_lap_seconds",
        "avg_lap_seconds",
        "valid_laps",
    ]:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

    data = data.dropna(
        subset=["full_name", "session_key", "fastest_lap_seconds"]
    )

    # Normalizzazione rispetto al miglior giro di ogni GP
    race_best = data.groupby("session_key")[
        "fastest_lap_seconds"
    ].transform("min")

    data["gap_percentage"] = (
        (data["fastest_lap_seconds"] - race_best)
        / race_best * 100
    )

    drivers = sorted(data["full_name"].unique())

    col1, col2 = st.columns(2)

    with col1:
        driver_a = st.selectbox(
            "Driver A",
            drivers,
            index=0,
        )

    with col2:
        driver_b = st.selectbox(
            "Driver B",
            drivers,
            index=1 if len(drivers) > 1 else 0,
        )

    if driver_a == driver_b:
        st.warning("Select two different drivers.")
        st.stop()

    mode = st.radio(
        "Comparison Mode",
        ["Season", "Grand Prix"],
        horizontal=True,
    )

    a = data[data["full_name"] == driver_a].copy()
    b = data[data["full_name"] == driver_b].copy()

    if mode == "Season":
        # Consideriamo soltanto i GP comuni
        common_sessions = sorted(
            set(a["session_key"]) & set(b["session_key"])
        )

        if not common_sessions:
            st.warning("No common Grand Prix found.")
            return

        a = a[a["session_key"].isin(common_sessions)]
        b = b[b["session_key"].isin(common_sessions)]

        a_avg = a["gap_percentage"].mean()
        b_avg = b["gap_percentage"].mean()

        a_wins = 0
        b_wins = 0

        merged = a[
            ["session_key", "circuit", "gap_percentage"]
        ].merge(
            b[["session_key", "gap_percentage"]],
            on="session_key",
            suffixes=("_a", "_b"),
        )

        a_wins = int(
            (merged["gap_percentage_a"]
             < merged["gap_percentage_b"]).sum()
        )

        b_wins = int(
            (merged["gap_percentage_b"]
             < merged["gap_percentage_a"]).sum()
        )

        st.subheader("Season Head-to-Head")

        c1, c2, c3 = st.columns(3)

        c1.metric("Common Grand Prix", len(common_sessions))
        c2.metric(f"{driver_a} Faster", a_wins)
        c3.metric(f"{driver_b} Faster", b_wins)

        st.divider()

        st.subheader("Average Gap to Race Best")

        c1, c2 = st.columns(2)
        c1.metric(driver_a, f"{a_avg:.2f}%")
        c2.metric(driver_b, f"{b_avg:.2f}%")

        # Grafico confronto GP per GP
        chart_data = pd.concat(
            [
                a.assign(driver=driver_a),
                b.assign(driver=driver_b),
            ],
            ignore_index=True,
        )

        # Ordine cronologico con session_key
        race_order = (
            chart_data[
                ["session_key", "circuit"]
            ]
            .drop_duplicates()
            .sort_values("session_key")
        )

        fig = px.line(
            chart_data,
            x="circuit",
            y="gap_percentage",
            color="driver",
            markers=True,
            category_orders={
                "circuit": race_order["circuit"].tolist()
            },
            labels={
                "circuit": "Grand Prix",
                "gap_percentage": "Gap to Race Best (%)",
                "driver": "Driver",
            },
        )

        fig.update_layout(
            height=500,
            xaxis_tickangle=-45,
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Grand Prix Comparison")

        table = merged.copy()

        table = table.rename(
            columns={
                "gap_percentage_a": f"{driver_a} Gap (%)",
                "gap_percentage_b": f"{driver_b} Gap (%)",
            }
        )

        st.dataframe(
            table[
                [
                    "circuit",
                    f"{driver_a} Gap (%)",
                    f"{driver_b} Gap (%)",
                ]
            ],
            hide_index=True,
            use_container_width=True,
        )

    else:
        # Confronto per singolo Gran Premio
        common_sessions = (
            set(a["session_key"]) & set(b["session_key"])
        )

        races = (
            data[data["session_key"].isin(common_sessions)]
            [["session_key", "country", "circuit"]]
            .drop_duplicates()
            .sort_values("session_key")
        )

        race_options = {
            f"{row.country} — {row.circuit}": row.session_key
            for row in races.itertuples()
        }

        if not race_options:
            st.warning("No common Grand Prix found.")
            return

        selected_race = st.selectbox(
            "Select Grand Prix",
            list(race_options.keys()),
        )

        session_key = race_options[selected_race]

        race_data = data[
            (data["session_key"] == session_key)
            & (data["full_name"].isin([driver_a, driver_b]))
        ].copy()

        st.subheader(selected_race)

        c1, c2 = st.columns(2)

        row_a = race_data[
            race_data["full_name"] == driver_a
        ].iloc[0]

        row_b = race_data[
            race_data["full_name"] == driver_b
        ].iloc[0]

        c1.metric(
            f"{driver_a} — Fastest Lap",
            f"{row_a['fastest_lap_seconds']:.3f} s",
        )

        c2.metric(
            f"{driver_b} — Fastest Lap",
            f"{row_b['fastest_lap_seconds']:.3f} s",
        )

        delta = (
            row_a["fastest_lap_seconds"]
            - row_b["fastest_lap_seconds"]
        )

        st.metric(
            "Fastest Lap Difference (A − B)",
            f"{delta:+.3f} s",
        )

        fig = px.bar(
            race_data,
            x="full_name",
            y="fastest_lap_seconds",
            color="full_name",
            labels={
                "full_name": "Driver",
                "fastest_lap_seconds": "Fastest Lap (s)",
            },
        )

        fig.update_layout(
            height=450,
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Detailed Statistics")

        st.dataframe(
            race_data[
                [
                    "full_name",
                    "team_name",
                    "valid_laps",
                    "fastest_lap_seconds",
                    "avg_lap_seconds",
                    "lap_stddev_seconds",
                ]
            ],
            hide_index=True,
            use_container_width=True,
        )

    st.caption(
        "Comparison based on recorded lap times, "
        "not official race finishing positions. "
        "Season comparisons include only Grand Prix "
        "with data for both selected drivers."
    )