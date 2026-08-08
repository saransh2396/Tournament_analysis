import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Dashboard", layout="wide")

st.title("Football Analytics Dashboard")

st.subheader("Upload Your Dataset")

uploaded = st.file_uploader("Upload CSV", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)

    if "Team" not in df.columns:
        st.error("❌ 'Team' column not found")
    else:
        st.session_state.df = df
        st.success(f"✅ Loaded {len(df)} teams")

        st.info("👉 Go to **League Analysis** or **Team Analysis** from sidebar")