
import streamlit as st

st.set_page_config(
    page_title="SmartAviatorAI",
    page_icon="✈️",
    layout="centered"
)

st.title("✈️ SmartAviatorAI")
st.subheader("Your Smart Aviation Assistant")

st.write(
    "Welcome to SmartAviatorAI! "
    "Your intelligent assistant for aviation information."
)

st.markdown("---")

st.header("How can I help you today?")

question = st.text_input(
    "Ask your aviation question:"
)

if st.button("Ask SmartAviatorAI"):
    if question:
        st.info("Your question: " + question)
        st.success(
            "SmartAviatorAI is ready to assist you. "
            "AI connection will be added next."
        )
    else:
        st.warning("Please enter your question.")

st.markdown("---")
st.caption("SmartAviatorAI © 2026")

