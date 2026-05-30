"""Streamlit dashboard skeleton for PR #1."""

from __future__ import annotations

import os
from datetime import date

import httpx
import streamlit as st

BACKEND_URL = os.getenv("DASHBOARD_BACKEND_URL", "http://localhost:8000")


def fetch_health() -> dict[str, str]:
    try:
        response = httpx.get(f"{BACKEND_URL}/health", timeout=3.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return {"status": "unavailable", "detail": str(exc)}


def main() -> None:
    st.set_page_config(page_title="舆情风险监测", page_icon="📊", layout="wide")

    st.title("舆情风险监测与日报生成系统")
    st.caption("PR #1 foundation: dashboard shell, backend health, and planned workflow.")

    with st.sidebar:
        st.header("导航")
        page = st.radio("页面", ["总览", "分析运行", "日报归档"], label_visibility="collapsed")
        selected_date = st.date_input("报告日期", value=date.today())

    health = fetch_health()
    status = health.get("status", "unknown")

    cols = st.columns(3)
    cols[0].metric("后端状态", status)
    cols[1].metric("报告日期", selected_date.isoformat())
    cols[2].metric("LLM 模式", "Mock")

    if status != "ok":
        st.warning("后端暂不可用。请先运行 FastAPI 服务。")
    else:
        st.success(f"已连接后端：{health.get('service', 'backend')}")

    if page == "总览":
        st.subheader("今日舆情概览")
        st.info("后续 PR 将在此展示情感分布、话题排行、风险排行和代表性证据。")
    elif page == "分析运行":
        st.subheader("分析运行状态")
        st.info("后续 PR 将展示采集、预处理、LLM 分析、风险评分和报告生成进度。")
    else:
        st.subheader("日报归档")
        st.info("后续 PR 将支持 Markdown、HTML 和 PDF 报告下载。")


if __name__ == "__main__":
    main()
