# app.py

import os
import glob
import re

import pandas as pd
import streamlit as st

# --- HARD-CODED SETTINGS ---
START_TIME = pd.to_datetime("2025-04-01 21:53:33")
FILENAME_PATTERN = re.compile(r"^phantom_p\d+_visibility_and_dose\.csv$")


def scan_and_plot():
    # find all CSVs in the working dir
    all_files = glob.glob("*.csv")
    files = [
        f for f in sorted(all_files)
        if FILENAME_PATTERN.fullmatch(os.path.basename(f))
    ]

    if not files:
        st.warning("❗ No matching CSVs found.")
        return

    # build one DataFrame: index = timestamp, columns = one person each
    df_all = pd.DataFrame()
    skipped = []

    for f in files:
        try:
            df = pd.read_csv(f)
            cols = df.columns.tolist()

            # detect your columns
            time_col = next((c for c in cols if "time" in c.lower()), cols[0])
            dose_col = next((c for c in cols if "dose" in c.lower()), cols[1] if len(cols) > 1 else cols[0])

            # interpret time_col as elapsed seconds
            elapsed = df[time_col].astype(float)
            ts = START_TIME + pd.to_timedelta(elapsed, unit="s")

            # extract the already‐cumulative dose
            dose = df[dose_col].astype(float)

            # label from filename, e.g. “P3”
            m = re.search(r"p(\d+)", os.path.basename(f), re.IGNORECASE)
            label = f"P{m.group(1)}" if m else os.path.basename(f)

            # make a Series and concat into df_all
            ser = pd.Series(dose.values, index=ts, name=label)
            df_all = pd.concat([df_all, ser], axis=1)
        except Exception as e:
            skipped.append(f"{f}: {e}")

    # plot
    if not df_all.empty:
        st.line_chart(df_all)

    # report skips
    if skipped:
        st.warning("⚠️ Some files were skipped:\n" + "\n".join(skipped))


def main():
    st.title("🔬 Cumulative Dose vs Time")
    st.write(f"Pattern: `{FILENAME_PATTERN.pattern}`  Start at **{START_TIME}**")
    if st.button("🔍 Scan & Plot"):
        scan_and_plot()


if __name__ == "__main__":
    main()
