
import streamlit as st
import pandas as pd
import sqlite3
import math
from pathlib import Path
from datetime import datetime, timezone

# ==========================================
# SMARTAVIATORAI V4.0 - SQLITE EDITION
# ==========================================

st.set_page_config(
    page_title="SmartAviatorAI V4.0",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DB_PATH = Path(__file__).resolve().parent / "smartaviator.db"

# ==========================================
# SQLITE DATABASE
# ==========================================

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                multiplier REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


initialize_database()


def save_rounds(values):
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO rounds (multiplier, created_at) VALUES (?, ?)",
            [(float(value), now) for value in values]
        )


def load_data():
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT id, multiplier, created_at FROM rounds ORDER BY id DESC",
            conn
        )

    if not df.empty:
        df["id"] = pd.to_numeric(df["id"], errors="coerce")
        df["multiplier"] = pd.to_numeric(
            df["multiplier"], errors="coerce"
        )
        df["created_at"] = pd.to_datetime(
            df["created_at"], utc=True, errors="coerce"
        )

        df = df.dropna(
            subset=["id", "multiplier", "created_at"]
        )

    return df.reset_index(drop=True)


def clear_data():
    with get_connection() as conn:
        conn.execute("DELETE FROM rounds")
        conn.execute(
            "DELETE FROM sqlite_sequence WHERE name='rounds'"
        )


def validate_values(values):
    if not values:
        raise ValueError("Ingiza angalau multiplier moja.")

    for value in values:
        if (
            not math.isfinite(float(value))
            or float(value) < 1
        ):
            raise ValueError(
                "Multiplier lazima iwe 1.00 au zaidi."
            )

    return values


# ==========================================
# MOBILE DESIGN
# ==========================================

st.markdown("""
<style>
.block-container {
    max-width: 850px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

.main-title {
    text-align: center;
    font-size: 30px;
    font-weight: 800;
}

.subtitle {
    text-align: center;
    color: #888;
    margin-bottom: 25px;
}

div.stButton > button {
    width: 100%;
    border-radius: 12px;
    min-height: 48px;
    font-weight: 700;
}

div[data-testid="stMetric"] {
    background: rgba(128,128,128,0.08);
    padding: 12px;
    border-radius: 12px;
}

@media(max-width:600px) {
    .main-title {
        font-size: 25px;
    }
    .block-container {
        padding-left: .7rem;
        padding-right: .7rem;
    }
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# HEADER
# ==========================================

st.markdown(
    '<div class="main-title">✈️ SmartAviatorAI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Professional Aviator Analytics | V4.0</div>',
    unsafe_allow_html=True
)

st.warning(
    "Aviator ni mchezo wa bahati nasibu. "
    "Historia ya matokeo haiwezi kutabiri kwa uhakika "
    "round inayofuata."
)


# ==========================================
# NAVIGATION
# ==========================================

menu = st.selectbox(
    "SYSTEM MENU",
    [
        "📊 Dashboard",
        "📈 Trend Analysis",
        "🧠 Advanced Analysis",
        "📋 Round History",
        "⚙️ Settings"
    ]
)


# ==========================================
# DATA INPUT
# ==========================================

st.header("📥 Ingiza Matokeo")

manual = st.text_area(
    "Weka multipliers ukitenganisha kwa koma",
    placeholder="1.20, 2.50, 1.05, 4.80"
)

uploaded = st.file_uploader(
    "Au upload CSV",
    type=["csv"]
)

if st.button("💾 SAVE RESULTS", type="primary"):

    try:
        values = []

        if manual.strip():
            manual_values = [
                float(x.strip())
                for x in manual.split(",")
                if x.strip()
            ]
            values.extend(manual_values)

        if uploaded is not None:
            csv_df = pd.read_csv(uploaded)

            if "multiplier" not in csv_df.columns:
                raise ValueError(
                    "CSV lazima iwe na column inayoitwa multiplier."
                )

            csv_values = pd.to_numeric(
                csv_df["multiplier"],
                errors="coerce"
            )

            if csv_values.isna().any():
                raise ValueError(
                    "CSV ina thamani zisizo sahihi."
                )

            values.extend(csv_values.tolist())

        values = validate_values(values)

        save_rounds(values)

        st.success(
            f"Rounds {len(values)} zimehifadhiwa kwenye SQLite!"
        )

        st.rerun()

    except ValueError as e:
        st.error(str(e))

    except Exception as e:
        st.error(f"Hitilafu wakati wa kuhifadhi: {e}")


# ==========================================
# LOAD DATA
# ==========================================

try:
    df = load_data()

except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

values = (
    df["multiplier"].astype(float)
    if not df.empty
    else pd.Series(dtype=float)
)


# ==========================================
# DASHBOARD
# ==========================================

if menu == "📊 Dashboard":

    st.header("📊 Main Dashboard")

    if df.empty:

        st.info(
            "Bado hakuna matokeo. Ingiza multipliers kwanza."
        )

    else:

        st.metric("TOTAL ROUNDS", len(df))

        c1, c2 = st.columns(2)

        c1.metric(
            "AVERAGE",
            f"{values.mean():.2f}x"
        )

        c2.metric(
            "MEDIAN",
            f"{values.median():.2f}x"
        )

        c3, c4 = st.columns(2)

        c3.metric(
            "HIGHEST",
            f"{values.max():.2f}x"
        )

        c4.metric(
            "LOWEST",
            f"{values.min():.2f}x"
        )

        st.subheader("📈 Historical Trend")

        chart_df = df.sort_values("id")

        st.line_chart(
            chart_df.set_index("id")["multiplier"]
        )

        st.subheader("📉 Distribution")

        for level in [1.5, 2, 3, 5, 10]:

            count = int((values >= level).sum())

            percentage = count / len(values) * 100

            st.write(
                f"Rounds ≥ {level}x: "
                f"{count} ({percentage:.1f}%)"
            )


# ==========================================
# TREND ANALYSIS
# ==========================================

elif menu == "📈 Trend Analysis":

    st.header("📈 Trend Analysis")

    if df.empty:

        st.info("Ingiza multipliers kwanza.")

    else:

        recent = values.head(50)

        st.metric(
            "Recent Average",
            f"{recent.mean():.2f}x"
        )

        st.line_chart(
            recent.iloc[::-1].reset_index(drop=True)
        )

        st.subheader("Multiplier Categories")

        categories = {
            "Low (1x - 1.99x)": (
                (recent >= 1) & (recent < 2)
            ),
            "Medium (2x - 4.99x)": (
                (recent >= 2) & (recent < 5)
            ),
            "High (5x - 9.99x)": (
                (recent >= 5) & (recent < 10)
            ),
            "Very High (10x+)": recent >= 10
        }

        for name, mask in categories.items():

            count = int(mask.sum())

            st.write(
                f"{name}: {count} rounds "
                f"({count / len(recent) * 100:.1f}%)"
            )


# ==========================================
# ADVANCED ANALYSIS
# ==========================================

elif menu == "🧠 Advanced Analysis":

    st.header("🧠 Advanced Statistical Analysis")

    if df.empty:

        st.info("Ingiza multipliers kwanza.")

    else:

        period = st.selectbox(
            "Analysis Period",
            [20, 50, 100, 500]
        )

        recent = values.head(period)

        a, b, c = st.columns(3)

        a.metric("Average", f"{recent.mean():.2f}x")
        b.metric("Median", f"{recent.median():.2f}x")
        c.metric("Highest", f"{recent.max():.2f}x")

        st.subheader("📊 Recent Trend")

        st.line_chart(
            recent.iloc[::-1].reset_index(drop=True)
        )

        # Consecutive rounds below 2x
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

        if len(recent) > 1:

            st.metric(
                "Standard Deviation",
                f"{recent.std():.2f}"
            )

        distribution = []

        for level in [1.5, 2, 3, 5, 10]:

            count = int((recent >= level).sum())

            distribution.append({
                "Multiplier": f"{level}x",
                "Rounds": count,
                "Percentage": round(
                    count / len(recent) * 100, 2
                )
            })

        st.dataframe(
            pd.DataFrame(distribution),
            use_container_width=True,
            hide_index=True
        )

        st.warning(
            "Takwimu hizi zinaeleza historia tu; "
            "hazitabiri round inayofuata."
        )


# ==========================================
# ROUND HISTORY
# ==========================================

elif menu == "📋 Round History":

    st.header("📋 Round History")

    if df.empty:

        st.info("Hakuna historia bado.")

    else:

        limit = st.selectbox(
            "History Size",
            [20, 50, 100, 500]
        )

        st.dataframe(
            df.head(limit),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ DOWNLOAD CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="smartaviator_history.csv",
            mime="text/csv",
            use_container_width=True
        )


# ==========================================
# SETTINGS
# ==========================================

elif menu == "⚙️ Settings":

    st.header("⚙️ Settings")

    st.metric("TOTAL SAVED ROUNDS", len(df))

    st.success("Database: SQLite")

    st.write("System Version: SmartAviatorAI V4.0")

    st.write("Storage: Local SQLite Database")

    st.divider()

    st.subheader("📥 Database Backup")

    if not df.empty:

        st.download_button(
            "⬇️ DOWNLOAD BACKUP CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="smartaviator_backup.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info("Hakuna data ya kufanya backup.")

    st.divider()

    st.subheader("⚠️ Delete All History")

    confirm = st.checkbox(
        "Nimeelewa kuwa kufuta kutafuta historia yote."
    )

    if st.button(
        "🗑️ DELETE ALL HISTORY",
        disabled=not confirm
    ):

        clear_data()

        st.success("Historia yote imefutwa.")

        st.rerun()


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "✈️ SmartAviatorAI Version 4.0 | "
    "Historical Statistics & Analytics"
)
