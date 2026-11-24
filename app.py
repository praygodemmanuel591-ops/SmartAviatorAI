
import streamlit as st
import pandas as pd
import requests
import math
from datetime import datetime, timezone

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="SmartAviatorAI",
    page_icon="✈️",
    layout="wide"
)

# =====================================
# SUPABASE REST API
# =====================================

@st.cache_resource
def get_config():
    url = st.secrets["SUPABASE_URL"].rstrip("/")
    key = st.secrets["SUPABASE_KEY"]

    return {
        "url": url,
        "headers": {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    }

try:
    config = get_config()
    API = config["url"] + "/rest/v1/rounds"
    HEADERS = config["headers"]

except Exception:
    st.error("Supabase Secrets hazijajazwa vizuri.")
    st.stop()


# =====================================
# DATABASE FUNCTIONS
# =====================================

def save_rounds(values):
    now = datetime.now(timezone.utc).isoformat()

    records = [
        {
            "multiplier": float(v),
            "created_at": now
        }
        for v in values
    ]

    response = requests.post(
        API,
        headers=HEADERS,
        json=records,
        timeout=30
    )

    response.raise_for_status()


def load_data():
    response = requests.get(
        API,
        headers=HEADERS,
        params={
            "select": "*",
            "order": "id.desc",
            "limit": "10000"
        },
        timeout=30
    )

    response.raise_for_status()

    return pd.DataFrame(response.json())


def clear_data():
    response = requests.delete(
        API,
        headers=HEADERS,
        params={"id": "gte.0"},
        timeout=30
    )

    response.raise_for_status()


# =====================================
# HEADER
# =====================================

st.title("✈️ SmartAviatorAI")

st.subheader(
    "Professional Aviator Analytics System"
)

st.success("🌐 Database connection configured")

st.warning(
    "Aviator ni mchezo wa bahati nasibu. "
    "Historia haiwezi kutabiri kwa uhakika "
    "matokeo ya round inayofuata."
)


# =====================================
# SIDEBAR
# =====================================

st.sidebar.title("✈️ SmartAviatorAI")

menu = st.sidebar.radio(
    "SYSTEM MENU",
    [
        "📊 Dashboard",
        "📈 Trend Analysis",
        "🧠 Advanced Analysis",
        "📋 Round History",
        "⚙️ Settings"
    ]
)

st.sidebar.caption("Version 3.0")


# =====================================
# INPUT RESULTS
# =====================================

st.header("📥 Enter Aviator Results")

manual = st.text_area(
    "Ingiza multipliers ukitenganisha kwa koma:",
    placeholder="1.20, 2.50, 1.05, 4.80"
)

uploaded = st.file_uploader(
    "Upload CSV yenye column multiplier",
    type=["csv"]
)

if st.button("💾 SAVE RESULTS", type="primary"):

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
            st.error("Multiplier lazima iwe 1.00 au zaidi.")

        else:
            save_rounds(values)

            st.success(
                f"Rounds {len(values)} zimehifadhiwa!"
            )

            st.rerun()

    except Exception as e:
        st.error(f"Hitilafu: {e}")


# =====================================
# LOAD DATABASE
# =====================================

try:
    df = load_data()

except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()


# =====================================
# DASHBOARD
# =====================================

values = pd.Series(dtype=float)

if not df.empty:
    values = df["multiplier"].astype(float)


if menu == "📊 Dashboard":

    st.header("📊 Main Dashboard")

    if df.empty:
        st.info("Bado hakuna matokeo yaliyohifadhiwa.")

    else:

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("TOTAL ROUNDS", len(df))
        c2.metric("AVERAGE", f"{values.mean():.2f}x")
        c3.metric("MEDIAN", f"{values.median():.2f}x")
        c4.metric("HIGHEST", f"{values.max():.2f}x")

        st.metric("LOWEST", f"{values.min():.2f}x")

        st.divider()

        st.subheader("📈 Historical Trend")

        st.line_chart(
            df.sort_values("id").set_index("id")["multiplier"]
        )

        st.subheader("📉 Multiplier Distribution")

        for level in [1.5, 2, 3, 5, 10]:

            count = int((values >= level).sum())
            percentage = count / len(values) * 100

            st.write(
                f"Rounds ≥ {level}x: "
                f"{count} ({percentage:.1f}%)"
            )

        st.caption(
            "Hizi ni takwimu za historia pekee."
        )


# =====================================
# TREND ANALYSIS
# =====================================

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


# =====================================
# ADVANCED ANALYSIS
# =====================================

elif menu == "🧠 Advanced Analysis":

    st.header("🧠 Advanced Statistical Analysis")

    if df.empty:
        st.info("Ingiza multipliers kwanza.")

    else:

        period = st.selectbox(
            "Choose analysis period",
            [20, 50, 100, 500]
        )

        recent = values.head(period)

        st.write(
            f"Rounds analyzed: {len(recent)}"
        )

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

        streak = 0

        for value in recent:
            if value < 2:
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

        st.subheader("Detailed Distribution")

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
            use_container_width=True
        )

        st.warning(
            "Uchambuzi huu hauwezi kutabiri "
            "matokeo ya round inayofuata."
        )


# =====================================
# ROUND HISTORY
# =====================================

elif menu == "📋 Round History":

    st.header("📋 Round History")

    if df.empty:
        st.info("Hakuna historia bado.")

    else:

        limit = st.selectbox(
            "Choose history size",
            [20, 50, 100, 500]
        )

        st.dataframe(
            df.head(limit),
            use_container_width=True
        )

        st.download_button(
            "⬇️ Download CSV",
            df.to_csv(index=False),
            file_name="smartaviator_history.csv",
            mime="text/csv"
        )


# =====================================
# SETTINGS
# =====================================

elif menu == "⚙️ Settings":

    st.header("⚙️ Settings")

    st.write(f"Total saved rounds: {len(df)}")

    st.subheader("Database")

    st.success("Supabase REST API configured")

    st.divider()

    st.subheader("⚠️ Delete All History")

    confirm = st.checkbox(
        "Nimeelewa kuwa kufuta kutafuta historia yote."
    )

    if st.button("🗑️ DELETE ALL HISTORY"):

        if confirm:

            try:
                clear_data()
                st.success("Historia yote imefutwa.")
                st.rerun()

            except Exception as e:
                st.error(f"Delete failed: {e}")

        else:
            st.warning("Thibitisha kwanza.")


# =====================================
# FOOTER
# =====================================

st.divider()

st.caption(
    "✈️ SmartAviatorAI Version 3.0 | "
    "Historical Statistics & Analytics | 2026"
)
