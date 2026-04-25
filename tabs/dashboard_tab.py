import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from utils.chart_builder import build_overview_charts


def render():
    st.markdown("""
    <div class="page-header">
        <h1>📈 Auto Dashboard</h1>
        <p class="page-sub">Beautiful charts auto-generated from your data.</p>
    </div>
    """, unsafe_allow_html=True)

    df = st.session_state.get("df_clean") if st.session_state.get("df_clean") is not None else st.session_state.get("df")
    if df is None:
        st.warning("⚠️ Please upload a file first.")
        if st.button("Go to Upload"):
            st.session_state.active_tab = "upload"
            st.rerun()
        return

    # Custom chart builder
    with st.expander("🎨 Build a Custom Chart", expanded=False):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(include="object").columns.tolist()
        date_cols = df.select_dtypes(include="datetime64").columns.tolist()
        all_cols = df.columns.tolist()

        cc1, cc2, cc3 = st.columns(3)
        chart_type = cc1.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie", "Box", "Histogram"])
        x_col = cc2.selectbox("X axis", all_cols, index=0)
        y_col = cc3.selectbox("Y axis", num_cols, index=0) if num_cols else None

        color_col = st.selectbox("Color by (optional)", ["None"] + cat_cols)
        color_arg = color_col if color_col != "None" else None

        if st.button("🔄  Generate Chart", type="primary"):
            try:
                if chart_type == "Bar":
                    fig = px.bar(df, x=x_col, y=y_col, color=color_arg,
                                 template="plotly_dark", color_discrete_sequence=[
                                     "#6366f1","#f59e0b","#10b981","#3b82f6","#ec4899"])
                elif chart_type == "Line":
                    fig = px.line(df.sort_values(x_col), x=x_col, y=y_col, color=color_arg,
                                  template="plotly_dark", markers=True)
                elif chart_type == "Scatter":
                    fig = px.scatter(df.sample(min(1000, len(df))), x=x_col, y=y_col,
                                     color=color_arg, template="plotly_dark", opacity=0.7)
                elif chart_type == "Pie":
                    vc = df[x_col].value_counts().head(12).reset_index()
                    vc.columns = [x_col, "count"]
                    fig = px.pie(vc, names=x_col, values="count", hole=0.4,
                                 template="plotly_dark")
                elif chart_type == "Box":
                    fig = px.box(df, x=color_arg, y=y_col, template="plotly_dark")
                elif chart_type == "Histogram":
                    fig = px.histogram(df, x=x_col, color=color_arg,
                                       template="plotly_dark", nbins=30)

                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Chart error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🤖 Auto-Generated Charts")

    with st.spinner("Building your dashboard..."):
        charts = build_overview_charts(df)

    if not charts:
        st.info("Not enough data to generate charts. Try a richer dataset.")
        return

    # Display charts in 2-column grid
    for i in range(0, len(charts), 2):
        cols = st.columns(2, gap="medium")
        for j, col in enumerate(cols):
            if i + j < len(charts):
                title, fig = charts[i + j]
                with col:
                    st.markdown(f'<div class="chart-card">', unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    # Correlation table if numeric cols
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if len(num_cols) >= 2:
        with st.expander("🔗 Full Correlation Table"):
            corr = df[num_cols].corr().round(3)
            st.dataframe(corr.style.background_gradient(cmap="RdYlGn", axis=None),
                         use_container_width=True)

    st.markdown("---")
    if st.button("💬  Ask Questions About Your Data", type="primary"):
        st.session_state.active_tab = "chat"
        st.rerun()
