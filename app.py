# app.py

import re
import io
import pandas as pd
import streamlit as st

# --- HARD-CODED SETTINGS ---
START_TIME = pd.to_datetime("2025-04-01 21:53:33")
FILENAME_PATTERN = re.compile(r"^phantom_p\d+_visibility_and_dose\.csv$")

def main():
    st.title("🔬 Cumulative Dose vs Time")

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

    if uploaded_files:
        df_all = pd.DataFrame()
        skipped = []

        for uploaded in uploaded_files:
            name = uploaded.name
            # skip non-matching names
            if not FILENAME_PATTERN.fullmatch(name):
                skipped.append(f"{name}: filename does not match pattern")
                continue

            try:
                # read CSV from in-memory buffer
                df = pd.read_csv(io.StringIO(uploaded.getvalue().decode()))
                cols = df.columns.tolist()

                # detect columns
                time_col = next((c for c in cols if "time" in c.lower()), cols[0])
                dose_col = next(
                    (c for c in cols if "dose" in c.lower()),
                    cols[1] if len(cols) > 1 else cols[0]
                )

                # elapsed seconds → timestamps
                elapsed = df[time_col].astype(float)
                timestamps = START_TIME + pd.to_timedelta(elapsed, unit="s")

                # already-cumulative dose
                dose = df[dose_col].astype(float)

                # series for this person
                m = re.search(r"p(\d+)", name, re.IGNORECASE)
                label = f"P{m.group(1)}" if m else name
                series = pd.Series(dose.values, index=timestamps, name=label)

                df_all = pd.concat([df_all, series], axis=1)

            except Exception as e:
                skipped.append(f"{name}: {e}")

        # plot
        if not df_all.empty:
            st.line_chart(df_all)

        # report skips
        if skipped:
            st.warning("⚠️ Some files were skipped:\n" + "\n".join(skipped))


if __name__ == "__main__":
    main()
