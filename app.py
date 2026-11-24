
import streamlit as st
import pandas as pd
import sqlite3
import math
from datetime import datetime, timezone

# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="SmartAviatorAI",
    page_icon="✈️",
    layout="wide"
)

DB = "aviator_history.db"

# =====================================
# DATABASE
# =====================================

def connect():
    return sqlite3.connect(DB)

def setup():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                multiplier REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def save_rounds(values):
    now = datetime.now(timezone.utc).isoformat()

    with connect() as con:
        con.executemany(
            """INSERT INTO rounds
            (multiplier, created_at)
            VALUES (?, ?)""",
            [(float(v), now) for v in values]
        )

def load_data():
    with connect() as con:
        return pd.read_sql_query(
            "SELECT * FROM rounds ORDER BY id DESC",
            con
        )

def clear_data():
    with connect() as con:
        con.execute("DELETE FROM rounds")

setup()

# =====================================
# HEADER
# =====================================

st.title("✈️ SmartAviatorAI")
st.subheader("Advanced Aviator Analysis System")

st.warning(
    "Aviator ni mchezo wa bahati nasibu. "
    "Historia haiwezi kuhakikisha au kujua "
    "multiplier ya round inayofuata."
)

# =====================================
# DATA INPUT
# =====================================

st.header("📥 Enter Aviator Results")

manual = st.text_area(
    "Ingiza multipliers ukitenganisha kwa koma:",
    placeholder="1.20, 2.50, 1.05, 4.80, 3.20"
)

uploaded = st.file_uploader(
    "Upload CSV with multiplier column",
    type=["csv"]
)

if st.button("💾 Save Results", type="primary"):

    values = []

    try:
        if manual.strip():
            values.extend([
                float(x.strip())
                for x in manual.split(",")
                if x.strip()
            ])

        if uploaded:
            file_df = pd.read_csv(uploaded)

            if "multiplier" not in file_df.columns:
                raise ValueError(
                    "CSV must contain multiplier column."
                )

            values.extend(
                pd.to_numeric(
                    file_df["multiplier"],
                    errors="coerce"
                ).dropna().tolist()
            )

        if not values:
            st.error("Enter at least one multiplier.")

        elif any(
            not math.isfinite(v) or v < 1
            for v in values
        ):
            st.error("Multipliers must be valid numbers >= 1.00.")

        else:
            save_rounds(values)
            st.success(
                f"{len(values)} results saved successfully!"
            )
            st.rerun()

    except ValueError as e:
        st.error(str(e))

    except Exception:
        st.error("Unable to process results.")

# =====================================
# LOAD DATABASE
# =====================================

df = load_data()

st.divider()
st.header("📊 Historical Dashboard")

if df.empty:

    st.info("No results saved yet.")

else:

    values = df["multiplier"].astype(float)

    # =================================
    # MAIN STATISTICS
    # =================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Rounds", len(df))
    c2.metric("Average", f"{values.mean():.2f}x")
    c3.metric("Median", f"{values.median():.2f}x")
    c4.metric("Highest", f"{values.max():.2f}x")

    st.metric("Lowest", f"{values.min():.2f}x")

    # =================================
    # HISTORY CHART
    # =================================

    st.subheader("📈 Multiplier History")

    chart_data = df.sort_values("id")

    st.line_chart(
        chart_data.set_index("id")["multiplier"]
    )

    # =================================
    # HISTORICAL DISTRIBUTION
    # =================================

    st.subheader("📉 Historical Distribution")

    for level in [1.5, 2, 3, 5, 10]:

        count = int((values >= level).sum())
        percentage = count / len(values) * 100

        st.write(
            f"Rounds ≥ {level}x: "
            f"{count} ({percentage:.1f}%)"
        )

    st.caption(
        "Hizi ni asilimia za historia, "
        "si uwezekano uliothibitishwa wa round ijayo."
    )

    # =================================
    # ADVANCED ANALYSIS
    # =================================

    st.divider()
    st.header("🧠 Advanced Aviator Analysis")

    period = st.selectbox(
        "Select analysis period",
        [20, 50, 100, 500],
        key="analysis_period"
    )

    recent = values.head(period)

    st.write(
        f"Rounds analyzed: {len(recent)}"
    )

    if len(recent) > 0:

        a, b, c = st.columns(3)

        a.metric(
            "Average",
            f"{recent.mean():.2f}x"
        )

        b.metric(
            "Median",
            f"{recent.median():.2f}x"
        )

        c.metric(
            "Highest",
            f"{recent.max():.2f}x"
        )

        st.subheader("📊 Recent Trend")

        st.line_chart(
            recent.iloc[::-1].reset_index(drop=True)
        )

        # =================================
        # STREAK ANALYSIS
        # =================================

        st.subheader("🔴 Low Multiplier Streak")

        streak = 0

        for value in recent:
            if value < 2:
                streak += 1
            else:
                break

        st.metric(
            "Consecutive rounds below 2x",
            streak
        )

        # =================================
        # DISTRIBUTION
        # =================================

        st.subheader("🔍 Detailed Distribution")

        distribution = []

        for level in [1.5, 2, 3, 5, 10]:

            count = int((recent >= level).sum())

            distribution.append({
                "Threshold": f"{level}x",
                "Rounds": count,
                "Percentage": round(
                    count / len(recent) * 100, 2
                )
            })

        st.dataframe(
            pd.DataFrame(distribution),
            use_container_width=True
        )

        # =================================
        # INTERPRETATION
        # =================================

        st.subheader("📋 Statistical Interpretation")

        st.write(
            f"Analysis average: {recent.mean():.2f}x"
        )

        st.write(
            f"Analysis standard deviation: "
            f"{recent.std():.2f}"
            if len(recent) > 1
            else "Standard deviation: Not available"
        )

        st.info(
            "Analysis describes historical results only. "
            "It cannot establish the next round outcome."
        )

    # =================================
    # ROUND HISTORY
    # =================================

    st.divider()
    st.header("📋 Round History")

    limit = st.selectbox(
        "Select history size",
        [20, 50, 100, 500],
        key="history_limit"
    )

    history = df.head(limit).copy()

    history.columns = [
        "Round ID",
        "Multiplier",
        "Date (UTC)"
    ]

    st.dataframe(
        history,
        use_container_width=True
    )

    # =================================
    # CSV EXPORT
    # =================================

    st.download_button(
        "⬇️ Download Full History",
        df.to_csv(index=False),
        file_name="smartaviator_history.csv",
        mime="text/csv"
    )

    # =================================
    # DATA MANAGEMENT
    # =================================

    st.divider()
    st.header("⚠️ Data Management")

    confirm = st.checkbox(
        "I understand this deletes all saved rounds."
    )

    if st.button("🗑️ Delete All History"):

        if confirm:
            clear_data()
            st.success("History deleted.")
            st.rerun()

        else:
            st.warning("Please confirm first.")

# =====================================
# LIVE DATA CONNECTION STATUS
# =====================================

st.divider()
st.header("🌐 Live Data Integration")

st.info(
    "Live API connection is not configured yet. "
    "A verified and authorized data provider is required."
)

st.caption(
    "SmartAviatorAI © 2026 | "
    "Historical Statistics & Analysis"
)
