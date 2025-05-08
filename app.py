# app.py

import os
import glob
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --- HARD-CODED SETTINGS ---
# Start time for timestamp conversion
START_TIME = pd.to_datetime("2025-04-01 21:53:33")

# Regex pattern for the CSV filenames you want to include
FILENAME_PATTERN = re.compile(r"^phantom_p\d+_visibility_and_dose\.csv$")


def scan_and_plot():
    # Find all CSV files in the working directory
    all_files = glob.glob("*.csv")
    # Filter by our hard-coded regex
    files = [f for f in sorted(all_files) if FILENAME_PATTERN.fullmatch(os.path.basename(f))]

    if not files:
        st.warning("❗️ No CSV files matching the pattern were found in the current directory.")
        return

    fig = go.Figure()
    skipped = []

    for f in files:
        try:
            df = pd.read_csv(f)
            cols = df.columns.tolist()

            # Detect columns
            time_col = next((c for c in cols if "time" in c.lower()), cols[0])
            dose_col = next((c for c in cols if "dose" in c.lower()),
                            cols[1] if len(cols) > 1 else cols[0])

            # Read elapsed‐seconds
            elapsed = df[time_col].astype(float)

            # Convert to actual timestamps
            ts = START_TIME + pd.to_timedelta(elapsed, unit="s")

            # Read (already cumulative) dose
            dose = df[dose_col].astype(float)

            # Derive a label like “P3” from “phantom_p3_…”
            m = re.search(r"p(\d+)", os.path.basename(f), re.IGNORECASE)
            label = f"P{m.group(1)}" if m else f

            fig.add_trace(
                go.Scatter(
                    x=ts,
                    y=dose,
                    mode="lines+markers",
                    name=label
                )
            )
        except Exception as e:
            skipped.append(f"{f}: {e}")

    fig.update_layout(
        title="Cumulative Dose vs Timestamp",
        xaxis_title="Timestamp",
        yaxis_title="Cumulative Dose",
        legend_title="Person",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    if skipped:
        st.warning("⚠️ Some files were skipped:\n" + "\n".join(skipped))


def main():
    st.title("🔬 Cumulative Dose vs Time Viewer")
    st.write(
        f"Scanning for files matching pattern `{FILENAME_PATTERN.pattern}` and plotting against "
        f"timestamps starting at **{START_TIME}**."
    )

    if st.button("🔍 Scan & Plot"):
        scan_and_plot()


if __name__ == "__main__":
    main()