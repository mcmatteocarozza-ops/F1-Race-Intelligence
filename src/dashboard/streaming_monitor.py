from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[2]
METRICS_PATH = BASE_DIR / "data/streaming/metrics"


def load_streaming_metrics():
    """Legge le metriche dei micro-batch elaborati da Spark."""

    batch_dirs = sorted(METRICS_PATH.glob("batch_*"))

    frames = []

    for batch_dir in batch_dirs:
        if not batch_dir.is_dir():
            continue

        # Ignora eventuali cartelle non ancora complete
        if not (batch_dir / "_SUCCESS").exists():
            continue

        try:
            frame = pd.read_parquet(batch_dir)
            frames.append(frame)
        except (OSError, ValueError):
            continue

    if not frames:
        return pd.DataFrame()

    return (
        pd.concat(frames, ignore_index=True)
        .sort_values("batch_id")
    )


@st.fragment(run_every="3s")
def render_live_metrics():
    metrics = load_streaming_metrics()

    if metrics.empty:
        st.info(
            "In attesa dei primi micro-batch elaborati da Spark..."
        )
        return

    total_events = int(metrics["events"].sum())
    total_batches = metrics["batch_id"].nunique()

    # Media ponderata sul numero di eventi per batch
    avg_speed = (
        (metrics["avg_speed"] * metrics["events"]).sum()
        / total_events
    )

    max_speed = metrics["max_speed"].max()

    st.subheader("Streaming Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Processed Events", f"{total_events:,}")
    c2.metric("Micro-Batches", total_batches)
    c3.metric("Average Speed", f"{avg_speed:.1f} km/h")
    c4.metric("Maximum Speed", f"{max_speed:.0f} km/h")

    st.divider()

    st.subheader("Speed Evolution")

    fig_speed = px.line(
        metrics,
        x="batch_id",
        y=["avg_speed", "max_speed"],
        markers=True,
        labels={
            "batch_id": "Micro-Batch",
            "value": "Speed (km/h)",
            "variable": "Metric"
        }
    )

    st.plotly_chart(fig_speed, use_container_width=True)

    st.subheader("RPM Evolution")

    fig_rpm = px.line(
        metrics,
        x="batch_id",
        y="avg_rpm",
        markers=True,
        labels={
            "batch_id": "Micro-Batch",
            "avg_rpm": "Average RPM"
        }
    )

    st.plotly_chart(fig_rpm, use_container_width=True)

    st.divider()

    st.subheader("Micro-Batch Details")

    st.dataframe(
        metrics[
            [
                "batch_id",
                "session_key",
                "driver_number",
                "events",
                "avg_speed",
                "max_speed",
                "avg_rpm"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Source: Spark Structured Streaming. "
        "Metrics are refreshed automatically every 3 seconds."
    )


def render_streaming_monitor():
    st.title("Live Streaming Monitor")

    st.caption(
        "Formula 1 — Spark Structured Streaming Telemetry Replay"
    )

    if not METRICS_PATH.exists():
        st.warning(
            "Streaming metrics directory not found."
        )
        return

    render_live_metrics()