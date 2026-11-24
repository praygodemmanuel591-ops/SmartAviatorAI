
import streamlit as st
import pandas as pd
import sqlite3
import math
from datetime import datetime, timezone

# ==========================================
# SMARTAVIATORAI - PROFESSIONAL DASHBOARD
# ==========================================

st.set_page_config(
    page_title="SmartAviatorAI",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = "aviator_history.db"

# ==========================================
# DESIGN
# ==========================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #07111f, #101d32);
}
[data-testid="stSidebar"] {
    background: #0b1728;
}
h1, h2, h3 {
    color: #eaf4ff !important;
}
p, label, span {
    color: #d5e1ef;
}
[data-testid="stMetric"] {
    background: #14263d;
    border: 1px solid #29445f;
    padding: 18px;
    border-radius: 12px;
}
div.stButton > button {
    border-radius: 9px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE
# ==========================================

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
            "INSERT INTO rounds (multiplier, created_at) VALUES (?, ?)",
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

# ==========================================
# HEADER
# ==========================================

st.title("✈️ SmartAviatorAI")

st.markdown(
    "### PROFESSIONAL AVIATOR ANALYTICS"
)

st.caption(
    "Historical Statistics • Trend Analysis • Data Management"
)

st.warning(
    "Aviator ni mchezo wa bahati nasibu. "
    "Takwimu za historia haziwezi kutabiri kwa uhakika "
    "matokeo ya round inayofuata."
)

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.title("✈️ SmartAviatorAI")
    st.markdown("---")

    st.markdown("### SYSTEM MENU")
    st.write("📊 Dashboard")
    st.write("📈 Trend Analysis")
    st.write("🧠 Advanced Analysis")
    st.write("📋 Round History")
    st.write("⚙️ Settings")

    st.markdown("---")
    st.caption("Version 2.0")
    st.caption("Analytics System")

# ==========================================
# INPUT SECTION
# ==========================================

st.header("📥 Enter Aviator Results")

with st.expander("Add New Rounds", expanded=True):

    manual = st.text_area(
        "Ingiza multipliers ukitenganisha kwa koma:",
        placeholder="1.20, 2.50, 1.05, 4.80, 3.20"
    )

    uploaded = st.file_uploader(
        "Upload CSV yenye column inayoitwa multiplier",
        type=["csv"]
    )

    if st.button("💾 SAVE RESULTS", type="primary",
                 use_container_width=True):

        values = []

        try:
            if manual.strip():
                values.extend([
                    float(x.strip())
                    for x in manual.replace("\n", ",").split(",")
                    if x.strip()
                ])

            if uploaded:
                file_df = pd.read_csv(uploaded)

                if "multiplier" not in file_df.columns:
                    raise ValueError(
                        "CSV lazima iwe na column ya multiplier."
                    )

                csv_values = pd.to_numeric(
                    file_df["multiplier"],
                    errors="coerce"
                ).dropna().tolist()

                values.extend(csv_values)

            if not values:
                st.error("Ingiza angalau multiplier moja.")

            elif any(
                not math.isfinite(v) or v < 1
                for v in values
            ):
                st.error(
                    "Multiplier lazima iwe namba halali ya 1.00 au zaidi."
                )

            else:
                save_rounds(values)
                st.success(
                    f"Rounds {len(values)} zimehifadhiwa!"
                )
                st.rerun()

        except ValueError as e:
            st.error(str(e))

        except Exception:
            st.error("Imeshindikana kusoma data.")

# ==========================================
# LOAD DATA
# ==========================================

df = load_data()

st.divider()

# ==========================================
# MAIN DASHBOARD
# ==========================================

st.header("📊 Main Dashboard")

if df.empty:

    st.info(
        "Hakuna rounds bado. Ingiza multipliers ili kuanza."
    )

else:

    values = df["multiplier"].astype(float)

    # MAIN METRICS

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "TOTAL ROUNDS",
        len(df)
    )

    c2.metric(
        "AVERAGE",
        f"{values.mean():.2f}x"
    )

    c3.metric(
        "MEDIAN",
        f"{values.median():.2f}x"
    )

    c4.metric(
        "HIGHEST",
        f"{values.max():.2f}x"
    )

    c5, c6, c7 = st.columns(3)

    c5.metric("LOWEST", f"{values.min():.2f}x")

    c6.metric(
        "ROUNDS ≥ 2x",
        f"{(values >= 2).sum()}"
    )

    c7.metric(
        "ROUNDS ≥ 5x",
        f"{(values >= 5).sum()}"
    )

    # ======================================
    # CHARTS
    # ======================================

    st.divider()
    st.header("📈 Historical Trend")

    chart_data = df.sort_values("id").copy()

    chart_data["Round"] = range(1, len(chart_data) + 1)

    st.line_chart(
        chart_data.set_index("Round")["multiplier"],
        height=320
    )

    st.subheader("📉 Multiplier Distribution")

    distribution = []

    for level in [1.5, 2, 3, 5, 10]:

        count = int((values >= level).sum())

        distribution.append({
            "Multiplier": f"{level}x and above",
            "Rounds": count,
            "Percentage": round(
                count / len(values) * 100, 2
            )
        })

    st.dataframe(
        pd.DataFrame(distribution),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Percentages represent historical observations, "
        "not guaranteed future probabilities."
    )

    # ======================================
    # ADVANCED ANALYSIS
    # ======================================

    st.divider()
    st.header("🧠 Advanced Statistical Analysis")

    period = st.selectbox(
        "Choose analysis period",
        [20, 50, 100, 500],
        index=0
    )

    recent = values.head(period)

    st.write(
        f"Rounds analyzed: {len(recent)}"
    )

    a, b, c = st.columns(3)

    a.metric("Recent Average", f"{recent.mean():.2f}x")
    b.metric("Recent Median", f"{recent.median():.2f}x")
    c.metric("Recent Highest", f"{recent.max():.2f}x")

    st.subheader("📊 Recent Round Trend")

    st.line_chart(
        recent.iloc[::-1].reset_index(drop=True),
        height=250
    )

    # LOW STREAK

    st.subheader("🔴 Low Multiplier Streak")

    streak = 0

    for value in recent:
        if value < 2:
            streak += 1
        else:
            break

    st.metric(
        "Consecutive recent rounds below 2x",
        streak
    )

    # STANDARD DEVIATION

    if len(recent) > 1:
        st.write(
            f"Standard deviation: {recent.std():.2f}"
        )

    # ======================================
    # RECENT DATA INTERPRETATION
    # ======================================

    st.subheader("📋 Statistical Interpretation")

    if recent.mean() >= 2:
        st.info(
            "Wastani wa multipliers katika kipindi "
            "kilichochaguliwa ni 2x au zaidi."
        )
    else:
        st.info(
            "Wastani wa multipliers katika kipindi "
            "kilichochaguliwa uko chini ya 2x."
        )

    st.warning(
        "Huu ni uchambuzi wa data iliyopita. "
        "Hauwezi kuthibitisha au kutabiri round inayofuata."
    )

    # ======================================
    # ROUND HISTORY
    # ======================================

    st.divider()
    st.header("📋 Round History")

    limit = st.selectbox(
        "Choose history size",
        [20, 50, 100, 500],
        key="history_size"
    )

    history = df.head(limit).copy()

    history.columns = [
        "Round ID",
        "Multiplier",
        "Date (UTC)"
    ]

    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True
    )

    # ======================================
    # DOWNLOAD
    # ======================================

    st.download_button(
        "⬇️ DOWNLOAD FULL HISTORY CSV",
        data=df.to_csv(index=False),
        file_name="smartaviator_history.csv",
        mime="text/csv",
        use_container_width=True
    )

    # ======================================
    # DATA MANAGEMENT
    # ======================================

    st.divider()
    st.header("⚙️ Data Management")

    confirm = st.checkbox(
        "I understand that deleting removes all saved rounds."
    )

    if st.button("🗑️ DELETE ALL HISTORY"):

        if confirm:
            clear_data()
            st.success("History deleted.")
            st.rerun()
        else:
            st.warning("Please confirm first.")

# ==========================================
# LIVE DATA
# ==========================================

st.divider()

st.header("🌐 Live Data Integration")

st.info(
    "Live connection: Not configured. "
    "An authorized and verified data provider is required."
)

st.write(
    "Future integration: Authorized data source, "
    "automatic round updates and historical synchronization."
)

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "✈️ SmartAviatorAI Version 2.0 | "
    "Historical Statistics & Analytics | 2026"
)
