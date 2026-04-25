"""
Auto-chart builder: picks the best chart type for each column combo.
Returns Plotly figures.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PALETTE = [
    "#6366f1", "#f59e0b", "#10b981", "#3b82f6",
    "#ec4899", "#f97316", "#06b6d4", "#8b5cf6",
    "#84cc16", "#ef4444",
]

TEMPLATE = "plotly_dark"

def _num_cols(df):
    return df.select_dtypes(include=[np.number]).columns.tolist()

def _cat_cols(df):
    return df.select_dtypes(include=["object", "category"]).columns.tolist()

def _date_cols(df):
    return df.select_dtypes(include=["datetime64"]).columns.tolist()


def build_overview_charts(df: pd.DataFrame) -> list:
    """Return a list of (title, fig) tuples for the dashboard."""
    charts = []
    num = _num_cols(df)
    cat = _cat_cols(df)
    dates = _date_cols(df)

    # 1. Distribution of first numeric column
    if num:
        col = num[0]
        fig = px.histogram(
            df, x=col, nbins=30,
            title=f"Distribution of {col}",
            color_discrete_sequence=[PALETTE[0]],
            template=TEMPLATE,
        )
        fig.update_layout(bargap=0.1, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)")
        charts.append((f"Distribution: {col}", fig))

    # 2. Bar chart of categorical col vs numeric col
    if cat and num:
        gc = cat[0]
        nc = num[0]
        top_cats = df[gc].value_counts().nlargest(15).index
        grp = (df[df[gc].isin(top_cats)]
               .groupby(gc)[nc]
               .sum()
               .sort_values(ascending=False)
               .reset_index())
        fig = px.bar(
            grp, x=gc, y=nc,
            title=f"{nc} by {gc}",
            color=nc,
            color_continuous_scale="Viridis",
            template=TEMPLATE,
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)")
        charts.append((f"{nc} by {gc}", fig))

    # 3. Pie chart for second categorical (if low cardinality)
    if len(cat) > 1:
        col2 = cat[1]
        if 2 <= df[col2].nunique() <= 12:
            vc = df[col2].value_counts().reset_index()
            vc.columns = [col2, "count"]
            fig = px.pie(
                vc, names=col2, values="count",
                title=f"Breakdown by {col2}",
                color_discrete_sequence=PALETTE,
                template=TEMPLATE,
                hole=0.4,
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            charts.append((f"Breakdown: {col2}", fig))
    elif cat:
        col2 = cat[0]
        if 2 <= df[col2].nunique() <= 12:
            vc = df[col2].value_counts().reset_index()
            vc.columns = [col2, "count"]
            fig = px.pie(
                vc, names=col2, values="count",
                title=f"Breakdown by {col2}",
                color_discrete_sequence=PALETTE,
                template=TEMPLATE,
                hole=0.4,
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            charts.append((f"Breakdown: {col2}", fig))

    # 4. Line chart over time
    if dates and num:
        dc = dates[0]
        nc = num[0]
        tmp = df.copy()
        tmp["_period"] = tmp[dc].dt.to_period("M").dt.to_timestamp()
        ts = tmp.groupby("_period")[nc].sum().reset_index()
        ts.columns = ["Period", nc]
        fig = px.line(
            ts, x="Period", y=nc,
            title=f"{nc} Over Time",
            markers=True,
            color_discrete_sequence=[PALETTE[2]],
            template=TEMPLATE,
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)")
        charts.append((f"{nc} Over Time", fig))

    # 5. Scatter: first two numeric columns
    if len(num) >= 2:
        x_col, y_col = num[0], num[1]
        color_col = cat[0] if cat else None
        fig = px.scatter(
            df.sample(min(500, len(df))),
            x=x_col, y=y_col,
            color=color_col,
            title=f"{y_col} vs {x_col}",
            color_discrete_sequence=PALETTE,
            template=TEMPLATE,
            opacity=0.7,
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)")
        charts.append((f"{y_col} vs {x_col}", fig))

    # 6. Correlation heatmap (if 3+ numeric cols)
    if len(num) >= 3:
        corr = df[num].corr().round(2)
        fig = px.imshow(
            corr,
            text_auto=True,
            title="Correlation Heatmap",
            color_continuous_scale="RdBu",
            template=TEMPLATE,
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        charts.append(("Correlation Heatmap", fig))

    # 7. Box plot for outlier visualization
    if num:
        cols_to_plot = num[:4]
        fig = go.Figure()
        for i, col in enumerate(cols_to_plot):
            fig.add_trace(go.Box(
                y=df[col].dropna(),
                name=col,
                marker_color=PALETTE[i % len(PALETTE)],
                boxmean=True,
            ))
        fig.update_layout(
            title="Box Plot — Spread & Outliers",
            template=TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        charts.append(("Spread & Outliers", fig))

    # 8. Top N bar (horizontal) for categorical
    if cat and num:
        gc = cat[0]
        nc = num[0]
        top = df.groupby(gc)[nc].sum().nlargest(10).reset_index()
        fig = px.bar(
            top, x=nc, y=gc, orientation="h",
            title=f"Top 10 {gc} by {nc}",
            color=nc,
            color_continuous_scale="Plasma",
            template=TEMPLATE,
        )
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        charts.append((f"Top 10 {gc}", fig))

    return charts
