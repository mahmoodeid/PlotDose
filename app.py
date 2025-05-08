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

    if not uploaded_files:
        return

    df_all = pd.DataFrame()
    skipped = []

    for uploaded in uploaded_files:
        name = uploaded.name
        # Skip non-matching names
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

            # read dose (already cumulative)
            dose = df[dose_col].astype(float)

            # detect if time_col is numeric (elapsed seconds) or timestamps
            try:
                elapsed = df[time_col].astype(float)
                # numeric => treat as elapsed seconds
                ts = START_TIME + pd.to_timedelta(elapsed, unit="s")
            except Exception:
                # not numeric => parse as datetime strings
                ts = pd.to_datetime(df[time_col])

            # build series
            m = re.search(r"p(\d+)", name, re.IGNORECASE)
            label = f"P{m.group(1)}" if m else name
            series = pd.Series(data=dose.values, index=ts, name=label)
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
