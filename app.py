
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="SmartAviatorAI",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ SmartAviatorAI")
st.subheader("Aviator Historical Analysis Dashboard")

st.warning(
    "Aviator ni mchezo wa bahati nasibu. "
    "Uchambuzi wa historia hauwezi kutabiri "
    "au kuhakikisha matokeo ya round inayofuata."
)

st.header("📥 Ingiza Multiplier")

values = st.text_area(
    "Andika multipliers, tenga kwa koma:",
    placeholder="1.20, 2.50, 1.05, 4.80, 3.20"
)

uploaded = st.file_uploader(
    "Au pakia CSV yenye column inayoitwa multiplier",
    type=["csv"]
)

data = []

if values.strip():
    try:
        data.extend([
            float(x.strip())
            for x in values.split(",")
            if x.strip()
        ])
    except ValueError:
        st.error("Tumia namba sahihi pekee.")

if uploaded:
    try:
        df = pd.read_csv(uploaded)
        if "multiplier" in df.columns:
            data.extend(
                pd.to_numeric(
                    df["multiplier"],
                    errors="coerce"
                ).dropna().tolist()
            )
        else:
            st.error("CSV lazima iwe na column ya multiplier.")
    except Exception:
        st.error("Imeshindikana kusoma CSV.")

data = [x for x in data if x >= 1.0 and np.isfinite(x)]

if data:
    df = pd.DataFrame({"Multiplier": data})

    st.header("📊 Historical Statistics")

    c1, c2, c3 = st.columns(3)

    c1.metric("Total rounds", len(data))
    c2.metric("Average", f"{np.mean(data):.2f}x")
    c3.metric("Median", f"{np.median(data):.2f}x")

    st.header("📈 Multiplier History")
    st.line_chart(df["Multiplier"])

    st.header("📉 Distribution")

    for level in [2, 5, 10]:
        count = sum(x >= level for x in data)
        percentage = count / len(data) * 100

        st.write(
            f"Rounds ≥ {level}x: "
            f"{count} ({percentage:.1f}%)"
        )

    st.header("🔎 Statistical Analysis")

    st.write(
        "Highest multiplier:",
        f"{max(data):.2f}x"
    )

    st.write(
        "Lowest multiplier:",
        f"{min(data):.2f}x"
    )

    st.info(
        "Takwimu hizi zinaeleza matokeo yaliyopita. "
        "Hazimaanishi kuwa round inayofuata itafikia "
        "multiplier fulani."
    )

else:
    st.info("Ingiza multipliers ili kuanza uchambuzi.")

st.caption("SmartAviatorAI © 2026")

