"""Streamlit dashboard entrypoint for the public opinion monitoring system."""

import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Public Opinion Risk Monitor",
    page_icon="📊",
    layout="wide",
)

st.title("LLM-enhanced Public Opinion Risk Monitor")
st.caption("Foundation dashboard for daily public opinion monitoring and risk reporting.")

with st.sidebar:
    st.header("System")
    st.write(f"Backend URL: `{BACKEND_URL}`")

st.subheader("Backend health")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    response.raise_for_status()
    health = response.json()
    st.success("Backend is reachable")
    st.json(health)
except requests.RequestException as exc:
    st.warning("Backend is not reachable yet. Start the FastAPI service and refresh.")
    st.code(str(exc))

st.subheader("Planned workflow")
st.markdown(
    """
    1. Ingest public opinion data from configured sources.
    2. Clean, normalize, deduplicate, and persist documents.
    3. Run structured mock/LLM analysis with evidence traceability.
    4. Score risk, aggregate trends, and generate daily reports.
    5. Review evidence, trends, and exports from this dashboard.
    """
)

col1, col2, col3 = st.columns(3)
col1.metric("Sources", "Planned")
col2.metric("Analysis mode", "Mock placeholder")
col3.metric("Reports", "Planned")
