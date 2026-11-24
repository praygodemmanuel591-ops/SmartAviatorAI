
import streamlit as st
import pandas as pd
import math
from datetime import datetime, timezone
from supabase import create_client

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="SmartAviatorAI",
    page_icon="✈️",
    layout="wide"
)

# =====================================
# SUPABASE CONNECTION
# =====================================

@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = get_supabase()
    connected = True
except Exception as e:
    connected = False
    st.error("Database connection failed. Check Streamlit Secrets.")
    st.stop()

# =====================================
# DATABASE FUNCTIONS
# =====================================

def save_rounds(values):
    records = [
        {
            "multiplier": float(v),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        for v in values
    ]

    for start in range(0, len(records), 500):
        supabase.table("rounds").insert(
            records[start:start + 500]
        ).execute()

def load_data():
    result = (
        supabase.table("rounds")
        .select("*")
        .order("id", desc=True)
        .limit(10000)
        .execute()
    )
    return pd.DataFrame(result.data)

def clear_data():
    supabase.table("rounds").delete().gte(
        "id", 0
    ).execute()

# =====================================
# HEADER
# =====================================

st.title("✈️ SmartAviatorAI")
st.subheader("Advanced Aviator Analysis System")

st.success("Supabase database connected successfully!")

st.warning(
    "Aviator ni mchezo wa bahati nasibu. "
    "Historia haiwezi kutabiri kwa uhakika "
    "matokeo ya round inayofuata."
)

# =====================================
# INPUT
# =====================================

st.header("📥 Enter Aviator Results")

manual = st.text_area(
    "Ingiza multipliers ukitenganisha kwa koma:",
    placeholder="1.20, 2.50, 1.05, 4.80"
)

uploaded = st.file_uploader(
    "Upload CSV yenye column ya multiplier",
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
            csv_df = pd.read_csv(uploaded)

            if "multiplier" not in csv_df.columns:
                raise ValueError(
                    "CSV lazima iwe na column multiplier."
                )

            values.extend(
                pd.to_numeric(
                    csv_df["multiplier"],
                    errors="coerce"
                ).dropna().tolist()
            )

        if not values:
            st.error("Ingiza angalau multiplier moja.")

        elif any(
            not math.isfinite(v) or v < 1
            for v in values
        ):
            st.error("Multiplier lazima iwe namba ya 1.00 au zaidi.")

        else:
            save_rounds(values)
            st.success(
                f"Rounds {len(values)} zimehifadhiwa Supabase!"
            )
            st.rerun()

    except ValueError as e:
        st.error(str(e))

    except Exception as e:
        st.error(f"Database error: {e}")

# =====================================
# LOAD DATA
# =====================================

try:
    df = load_data()
except Exception as e:
    st.error(f"Imeshindikana kusoma database: {e}")
    st.stop()

st.divider()
st.header("📊 Main Dashboard")

if df.empty:
    st.info("Bado hakuna rounds zilizohifadhiwa.")

else:
    values = df["multiplier"].astype(float)

    a, b, c, d = st.columns(4)

    a.metric("Total Rounds", len(df))
    b.metric("Average", f"{values.mean():.2f}x")
    c.metric("Median", f"{values.median():.2f}x")
    d.metric("Highest", f"{values.max():.2f}x")

    st.metric("Lowest", f"{values.min():.2f}x")

    # =================================
    # HISTORY CHART
    # =================================

    st.subheader("📈 Historical Trend")

    st.line_chart(
        df.sort_values("id").set_index("id")["multiplier"]
    )

    # =================================
    # DISTRIBUTION
    # =================================

    st.subheader("📉 Historical Distribution")

    for level in [1.5, 2, 3, 5, 10]:

        count = int((values >= level).sum())
        percent = count / len(values) * 100

        st.write(
            f"Rounds ≥ {level}x: "
            f"{count} ({percent:.1f}%)"
        )

    st.caption(
        "Asilimia hizi zinawakilisha historia pekee, "
        "si uwezekano wa round inayofuata."
    )

    # =================================
    # ADVANCED ANALYSIS
    # =================================

    st.divider()
    st.header("🧠 Advanced Statistical Analysis")

    period = st.selectbox(
        "Choose analysis period",
        [20, 50, 100, 500],
        key="analysis_period"
    )

    recent = values.head(period)

    st.write(f"Rounds analyzed: {len(recent)}")

    x, y, z = st.columns(3)

    x.metric("Recent Average", f"{recent.mean():.2f}x")
    y.metric("Recent Median", f"{recent.median():.2f}x")
    z.metric("Recent Highest", f"{recent.max():.2f}x")

    st.subheader("📊 Recent Round Trend")

    st.line_chart(
        recent.iloc[::-1].reset_index(drop=True)
    )

    streak = 0

    for v in recent:
        if v < 2:
            streak += 1
        else:
            break

    st.subheader("🔴 Low Multiplier Streak")

    st.metric(
        "Consecutive rounds below 2x",
        streak
    )

    if len(recent) > 1:
        st.write(
            f"Standard deviation: {recent.std():.2f}"
        )

    st.info(
        "Uchambuzi huu unaeleza matokeo yaliyopita. "
        "Hauwezi kujua au kuthibitisha multiplier ya round ijayo."
    )

    # =================================
    # ROUND HISTORY
    # =================================

    st.divider()
    st.header("📋 Round History")

    limit = st.selectbox(
        "Choose history size",
        [20, 50, 100, 500],
        key="history_limit"
    )

    history = df.head(limit).copy()

    st.dataframe(
        history,
        use_container_width=True
    )

    st.download_button(
        "⬇️ Download History CSV",
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
        "Nimeelewa kuwa kufuta kutafuta historia yote."
    )

    if st.button("🗑️ Delete All History"):

        if confirm:
            try:
                clear_data()
                st.success("Historia imefutwa.")
                st.rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")
        else:
            st.warning("Thibitisha kwanza.")

# =====================================
# STATUS
# =====================================

st.divider()

st.success("🌐 Supabase: Connected")

st.info(
    "Live Aviator prediction is not available. "
    "SmartAviatorAI provides historical statistical analysis only."
)

st.caption(
    "SmartAviatorAI © 2026 | Supabase Edition"
)
