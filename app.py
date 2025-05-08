# app.py

import re
import io

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# --- HARD-CODED SETTINGS ---
START_TIME = pd.to_datetime("2025-04-01 21:53:33")
FILENAME_PATTERN = re.compile(r"^phantom_p\d+_visibility_and_dose\.csv$")

def main():
    st.title("🔬 Cumulative Dose vs Time (Plotly)")

    st.markdown(
        f"""
        **Start time**: {START_TIME}  
        **Filename pattern**: `{FILENAME_PATTERN.pattern}`  
        Select all your matching CSVs below.
        """
    )

    uploaded_files = st.file_uploader(
        "📂 Select CSV files",
        type="csv",
        accept_multiple_files=True
    )

    if not uploaded_files:
        return

    fig = go.Figure()
    skipped = []

    for uploaded in uploaded_files:
        name = uploaded.name
        # skip non-matching files
        if not FILENAME_PATTERN.fullmatch(name):
            skipped.append(f"{name}: filename does not match pattern")
            continue

        try:
            raw = uploaded.getvalue().decode("utf-8")
            df = pd.read_csv(io.StringIO(raw))
            cols = df.columns.tolist()

            # detect columns
            time_col = next((c for c in cols if "time" in c.lower()), cols[0])
            dose_col = next(
                (c for c in cols if "dose" in c.lower()),
                cols[1] if len(cols) > 1 else cols[0]
            )

            # read (already cumulative) dose
            dose = df[dose_col].astype(float)

            # attempt numeric → elapsed seconds
            try:
                elapsed = df[time_col].astype(float)
                ts = START_TIME + pd.to_timedelta(elapsed, unit="s")
            except Exception:
                # fallback: parse as datetime strings
                ts = pd.to_datetime(df[time_col])

            # derive label, e.g. "P3"
            m = re.search(r"p(\d+)", name, re.IGNORECASE)
            label = f"P{m.group(1)}" if m else name

            # add trace
            fig.add_trace(go.Scatter(
                x=ts,
                y=dose,
                mode="lines+markers",
                name=label
            ))

        except Exception as e:
            skipped.append(f"{name}: {e}")

    fig.update_layout(
        title="Cumulative Dose vs Time",
        xaxis_title="Timestamp",
        yaxis_title="Cumulative Dose",
        legend_title="Person",
        template="plotly_white"
    )

    # display interactive Plotly chart
    st.plotly_chart(fig, use_container_width=True)

    if skipped:
        st.warning("⚠️ Some files were skipped:\n" + "\n".join(skipped))


if __name__ == "__main__":
    main()
