import streamlit as st
import pandas as pd
from utils.kpi_engine import compute_kpis


def _kpi_card(label, value, icon, color):
    return f"""
    <div class="kpi-card" style="border-top: 3px solid {color};">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value" style="color:{color};">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """


def render():
    st.markdown("""
    <div class="page-header">
        <h1>📊 Key Performance Indicators</h1>
        <p class="page-sub">Auto-detected KPIs from your data — no configuration needed.</p>
    </div>
    """, unsafe_allow_html=True)

    df = st.session_state.get("df_clean") or st.session_state.get("df")
    if df is None:
        st.warning("⚠️ Please upload a file first.")
        if st.button("Go to Upload"):
            st.session_state.active_tab = "upload"
            st.rerun()
        return

    kpis = compute_kpis(df)
    st.session_state.kpis = kpis

    # KPI grid
    st.markdown("### 🔢 Core Metrics")
    cols_per_row = 4
    rows = [kpis[i:i+cols_per_row] for i in range(0, len(kpis), cols_per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for col, kpi in zip(cols, row):
            with col:
                st.markdown(
                    _kpi_card(kpi["label"], kpi["value"], kpi["icon"], kpi["color"]),
                    unsafe_allow_html=True
                )

    # Detailed summaries
    st.markdown("---")
    st.markdown("### 📋 Detailed Summary Tables")

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include="object").columns.tolist()

    if num_cols:
        st.markdown("#### 📐 Numeric Columns — Statistics")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        desc = df[num_cols].describe().T.round(2)
        desc.index.name = "Column"
        st.dataframe(desc, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if cat_cols:
        st.markdown("#### 🏷️ Categorical Columns — Value Counts")
        selected_cat = st.selectbox("Select column to explore:", cat_cols)
        if selected_cat:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            vc = df[selected_cat].value_counts().reset_index()
            vc.columns = [selected_cat, "Count"]
            vc["Percentage"] = (vc["Count"] / len(df) * 100).round(1).astype(str) + "%"

            c1, c2 = st.columns([1, 2])
            with c1:
                st.dataframe(vc.head(20), use_container_width=True, hide_index=True)
            with c2:
                import plotly.express as px
                top = vc.head(10)
                fig = px.bar(
                    top, x="Count", y=selected_cat,
                    orientation="h",
                    color="Count",
                    color_continuous_scale="Viridis",
                    template="plotly_dark",
                    title=f"Top values in {selected_cat}",
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis={"categoryorder": "total ascending"},
                    showlegend=False,
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("➡️  View Full Dashboard", type="primary"):
        st.session_state.active_tab = "dashboard"
        st.rerun()
