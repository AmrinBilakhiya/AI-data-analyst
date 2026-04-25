import pandas as pd
import numpy as np
from typing import Any


def _pct_change(a, b):
    if b == 0:
        return None
    return round((a - b) / abs(b) * 100, 1)


def compute_kpis(df: pd.DataFrame) -> list[dict]:
    """
    Auto-detect and compute KPIs from any dataframe.
    Returns a list of dicts: {label, value, delta, icon, color}
    """
    kpis = []
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    obj_cols = df.select_dtypes(include=["object"]).columns.tolist()

    # Total rows
    kpis.append({
        "label": "Total Records",
        "value": f"{len(df):,}",
        "delta": None,
        "icon": "🗂️",
        "color": "#6366f1",
    })

    # For each numeric column — sum, mean, etc.
    revenue_keywords = ["revenue", "sales", "amount", "total", "income", "price",
                        "value", "spend", "cost", "profit", "gmv", "arr", "mrr"]
    count_keywords = ["count", "quantity", "qty", "units", "orders", "customers",
                      "transactions", "sessions", "visits", "clicks"]
    rate_keywords = ["rate", "ratio", "pct", "percent", "%", "score", "nps",
                     "margin", "growth", "churn", "conversion"]

    used_cols = set()

    def best_match(col, keywords):
        c = col.lower()
        return any(k in c for k in keywords)

    # Revenue-type KPIs
    for col in num_cols:
        if best_match(col, revenue_keywords) and col not in used_cols:
            total = df[col].sum()
            mean_val = df[col].mean()
            kpis.append({
                "label": f"Total {col.replace('_', ' ').title()}",
                "value": _fmt_number(total),
                "delta": None,
                "icon": "💰",
                "color": "#10b981",
            })
            kpis.append({
                "label": f"Avg {col.replace('_', ' ').title()}",
                "value": _fmt_number(mean_val),
                "delta": None,
                "icon": "📐",
                "color": "#f59e0b",
            })
            used_cols.add(col)
            if len(kpis) >= 9:
                break

    # Count-type KPIs
    for col in num_cols:
        if best_match(col, count_keywords) and col not in used_cols:
            total = df[col].sum()
            kpis.append({
                "label": f"Total {col.replace('_', ' ').title()}",
                "value": _fmt_number(total),
                "delta": None,
                "icon": "🔢",
                "color": "#3b82f6",
            })
            used_cols.add(col)
            if len(kpis) >= 9:
                break

    # Rate/Score KPIs
    for col in num_cols:
        if best_match(col, rate_keywords) and col not in used_cols:
            mean_val = df[col].mean()
            kpis.append({
                "label": f"Avg {col.replace('_', ' ').title()}",
                "value": f"{mean_val:.2f}",
                "delta": None,
                "icon": "📊",
                "color": "#ec4899",
            })
            used_cols.add(col)
            if len(kpis) >= 9:
                break

    # Remaining numeric columns
    for col in num_cols:
        if col not in used_cols and len(kpis) < 9:
            total = df[col].sum()
            kpis.append({
                "label": f"Total {col.replace('_', ' ').title()}",
                "value": _fmt_number(total),
                "delta": None,
                "icon": "📌",
                "color": "#8b5cf6",
            })
            used_cols.add(col)

    # Categorical columns — unique values
    for col in obj_cols[:2]:
        n = df[col].nunique()
        kpis.append({
            "label": f"Unique {col.replace('_', ' ').title()}s",
            "value": f"{n:,}",
            "delta": None,
            "icon": "🏷️",
            "color": "#06b6d4",
        })

    # Date range if available
    if date_cols:
        col = date_cols[0]
        mn, mx = df[col].min(), df[col].max()
        if pd.notna(mn) and pd.notna(mx):
            days = (mx - mn).days
            kpis.append({
                "label": "Date Range (days)",
                "value": f"{days:,}",
                "delta": None,
                "icon": "📅",
                "color": "#f97316",
            })

    return kpis[:12]  # max 12 KPI cards


def _fmt_number(val) -> str:
    if pd.isna(val):
        return "N/A"
    if abs(val) >= 1_000_000_000:
        return f"{val/1_000_000_000:.2f}B"
    if abs(val) >= 1_000_000:
        return f"{val/1_000_000:.2f}M"
    if abs(val) >= 1_000:
        return f"{val/1_000:.1f}K"
    if isinstance(val, float):
        return f"{val:.2f}"
    return f"{int(val):,}"
