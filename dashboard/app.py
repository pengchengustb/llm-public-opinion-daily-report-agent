"""Streamlit dashboard for public opinion risk monitoring."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import streamlit as st

BACKEND_URL = os.getenv("DASHBOARD_BACKEND_URL", "http://localhost:8000")


def fetch_health() -> dict[str, Any]:
    try:
        response = httpx.get(f"{BACKEND_URL}/health", timeout=3.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return {"status": "unavailable", "detail": str(exc)}


def fetch_dashboard_summary(selected_date: date) -> dict[str, Any]:
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/v1/dashboard/summary",
            params={"report_date": selected_date.isoformat()},
            timeout=5.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        return {"status": "unavailable", "detail": str(exc)}


def render_metrics(summary: dict[str, Any], selected_date: date, backend_status: str) -> None:
    metrics = summary.get("metrics", {})
    cols = st.columns(5)
    cols[0].metric("后端状态", backend_status)
    cols[1].metric("报告日期", selected_date.isoformat())
    cols[2].metric("情绪样本", metrics.get("sentiment_total", 0))
    cols[3].metric("风险条目", metrics.get("risk_count", 0))
    cols[4].metric("最高风险分", f"{metrics.get('highest_risk_score', 0):.2f}")


def render_overview(summary: dict[str, Any]) -> None:
    distribution = summary.get("sentiment_distribution", {})
    risks = summary.get("risks", [])
    topics = summary.get("topics", [])
    evidence = summary.get("evidence", [])

    left, right = st.columns([1, 1])
    with left:
        st.subheader("情绪分布")
        if distribution:
            st.bar_chart(distribution)
        else:
            st.info("暂无情绪分析结果")

    with right:
        st.subheader("风险排行")
        if risks:
            risk_rows = [
                {
                    "类别": risk["category"],
                    "等级": risk["severity"],
                    "确定性评分": risk["deterministic_score"],
                    "不确定性": risk["uncertainty_score"],
                }
                for risk in risks
            ]
            st.dataframe(risk_rows, use_container_width=True, hide_index=True)
        else:
            st.info("暂无风险评分结果")

    st.subheader("主题排行")
    if topics:
        topic_rows = [
            {
                "主题": topic["topic"],
                "增长分": topic["growth_score"],
                "关键词": "、".join(topic.get("keywords", [])),
                "摘要": topic["summary"],
            }
            for topic in topics
        ]
        st.dataframe(topic_rows, use_container_width=True, hide_index=True)
    else:
        st.info("暂无主题结果")

    st.subheader("代表证据")
    if evidence:
        for item in evidence:
            title = item["title"] or item["entity_type"]
            with st.expander(f"{title} · 互动 {item['engagement_score']}"):
                st.caption(f"证据 ID：{item['id']}")
                st.write(item["text"])
    else:
        st.info("暂无可追溯证据")


def render_runs(summary: dict[str, Any]) -> None:
    run = summary.get("latest_analysis_run")
    st.subheader("最近分析运行")
    if not run:
        st.info("暂无已完成的分析运行")
        return

    cols = st.columns(4)
    cols[0].metric("运行状态", run["status"])
    cols[1].metric("Provider", run["provider"])
    cols[2].metric("模型", run["model_name"])
    cols[3].metric("Mock 模式", "是" if run["mock_mode"] else "否")
    st.caption(f"Run ID：{run['id']}")
    st.json(run.get("runtime_metadata", {}))


def render_reports(summary: dict[str, Any]) -> None:
    reports = summary.get("reports", [])
    st.subheader("日报归档")
    if not reports:
        st.info("所选日期暂无日报")
        return

    for report in reports:
        st.markdown(f"### {report['title']}")
        st.caption(f"状态：{report['status']} · Report ID：{report['id']}")
        st.write(report["summary"])
        cols = st.columns(2)
        _render_download_button(
            cols[0],
            "下载 Markdown",
            report.get("markdown_path"),
            "text/markdown",
        )
        _render_download_button(cols[1], "下载 HTML", report.get("html_path"), "text/html")


def _render_download_button(container, label: str, file_path: str | None, mime: str) -> None:
    if not file_path:
        container.button(label, disabled=True, use_container_width=True)
        return

    path = Path(file_path)
    if not path.exists():
        container.warning(f"文件不存在：{file_path}")
        return

    container.download_button(
        label,
        data=path.read_bytes(),
        file_name=path.name,
        mime=mime,
        use_container_width=True,
    )


def main() -> None:
    st.set_page_config(page_title="舆情风险监测", page_icon="📊", layout="wide")

    st.title("舆情风险监测与日报生成系统")
    st.caption("结构化分析、风险评分、证据追溯和日报归档")

    with st.sidebar:
        st.header("导航")
        page = st.radio("页面", ["总览", "分析运行", "日报归档"], label_visibility="collapsed")
        selected_date = st.date_input("报告日期", value=date.today())

    health = fetch_health()
    backend_status = health.get("status", "unknown")
    summary = (
        fetch_dashboard_summary(selected_date)
        if backend_status == "ok"
        else {"status": "offline"}
    )

    render_metrics(summary, selected_date, backend_status)
    if backend_status != "ok":
        st.warning("后端暂不可用，请先运行 FastAPI 服务。")
        if health.get("detail"):
            st.caption(health["detail"])
        return

    if summary.get("status") == "empty":
        st.info("暂无已完成的分析运行。请先执行 seed、ingest、analyze 和 report 命令。")

    if page == "总览":
        render_overview(summary)
    elif page == "分析运行":
        render_runs(summary)
    else:
        render_reports(summary)


if __name__ == "__main__":
    main()
