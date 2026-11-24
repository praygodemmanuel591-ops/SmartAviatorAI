


import streamlit as st
import pandas as pd
import sqlite3
import math
from datetime import datetime, timezone

st.set_page_config(
    page_title="SmartAviatorAI",
    page_icon="✈️",
    layout="wide"
)

DB = "aviator_history.db"

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
    with connect() as con:
        con.executemany(
            "INSERT INTO rounds (multiplier, created_at) VALUES (?, ?)",
            [
                (float(v), datetime.now(timezone.utc).isoformat())
                for v in values
            ]
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

st.title("✈️ SmartAviatorAI")
st.subheader("Aviator Historical Analysis System")

st.warning(
    "Aviator ni mchezo wa bahati nasibu. "
    "Historia ya multipliers haiwezi kujua au kuhakikisha "
    "matokeo ya round inayofuata."
)

st.header("📥 Ingiza Matokeo")

manual = st.text_area(
    "Andika multipliers ukitenganisha kwa koma:",
    placeholder="1.20, 2.50, 1.05, 4.80"
)

uploaded = st.file_uploader(
    "Pakia CSV yenye column ya multiplier",
    type=["csv"]
)

if st.button("💾 Hifadhi Matokeo", type="primary"):
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
                    "CSV lazima iwe na column multiplier"
                )

            values.extend(
                pd.to_numeric(
                    file_df["multiplier"],
                    errors="coerce"
                ).dropna().tolist()
            )

        if not values:
            st.error("Weka angalau multiplier moja.")
        elif any(
            not math.isfinite(v) or v < 1
            for v in values
        ):
            st.error("Multipliers lazima ziwe namba za 1.00 au zaidi.")
        else:
            save_rounds(values)
            st.success(
                f"Matokeo {len(values)} yamehifadhiwa!"
            )
            st.rerun()

    except ValueError as e:
        st.error(str(e))
    except Exception:
        st.error("Imeshindikana kusoma data.")

df = load_data()

st.divider()
st.header("📊 Historical Dashboard")

if df.empty:
    st.info("Bado hakuna matokeo yaliyohifadhiwa.")
else:
    values = df["multiplier"]

    a, b, c, d = st.columns(4)

    a.metric("Total rounds", len(df))
    b.metric("Average", f"{values.mean():.2f}x")
    c.metric("Median", f"{values.median():.2f}x")
    d.metric("Highest", f"{values.max():.2f}x")

    st.subheader("📈 Multiplier History")

    st.line_chart(
        df.sort_values("id")["multiplier"]
    )

    st.subheader("📉 Probability in Historical Data")

    for level in [2, 5, 10]:
        count = int((values >= level).sum())
        percentage = count / len(values) * 100

        st.write(
            f"Rounds ≥ {level}x: "
            f"{count} ({percentage:.1f}%)"
        )

    st.caption(
        "Hizi ni asilimia za matokeo yaliyopita, "
        "si uwezekano uliothibitishwa wa round inayofuata."
    )

    st.subheader("📋 Round History")

    limit = st.selectbox(
        "Chagua idadi ya rounds",
        [20, 50, 100],
        index=0
    )

    history = df.head(limit).copy()
    history.columns = [
        "Round ID", "Multiplier", "Date (UTC)"
    ]

    st.dataframe(history, use_container_width=True)

    st.download_button(
        "⬇️ Pakua historia CSV",
        df.to_csv(index=False),
        file_name="smartaviator_history.csv",
        mime="text/csv"
    )

    st.divider()
    st.subheader("⚠️ Data Management")

    confirm = st.checkbox(
        "Nimeelewa kuwa kufuta kutafuta historia yote."
    )

    if st.button("Futa Historia Yote"):
        if confirm:
            clear_data()
            st.success("Historia imefutwa.")
            st.rerun()
        else:
            st.warning("Thibitisha kwanza.")

st.caption("SmartAviatorAI © 2026")
