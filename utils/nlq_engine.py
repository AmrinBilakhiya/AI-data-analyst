"""
Natural Language Query Engine — zero external API.
Uses rule-based NL parsing + pandas to answer questions about the dataframe.
"""

import re
import pandas as pd
import numpy as np
from typing import Any


# ── helpers ───────────────────────────────────────────────────────────────────

def _find_col(df: pd.DataFrame, hint: str) -> str | None:
    """Find the best matching column name for a keyword."""
    hint_l = hint.lower().strip()
    # exact match
    for c in df.columns:
        if c.lower() == hint_l:
            return c
    # contains match
    for c in df.columns:
        if hint_l in c.lower():
            return c
    # partial word match
    hint_words = set(hint_l.split())
    best, best_score = None, 0
    for c in df.columns:
        col_words = set(c.lower().replace("_", " ").split())
        score = len(hint_words & col_words)
        if score > best_score:
            best, best_score = c, score
    return best if best_score > 0 else None


def _num_cols(df):
    return df.select_dtypes(include=[np.number]).columns.tolist()

def _cat_cols(df):
    return df.select_dtypes(include=["object", "category"]).columns.tolist()

def _date_cols(df):
    return df.select_dtypes(include=["datetime64"]).columns.tolist()

def _fmt(val) -> str:
    if isinstance(val, float):
        if abs(val) >= 1_000_000:
            return f"{val:,.2f} ({val/1_000_000:.2f}M)"
        return f"{val:,.2f}"
    if isinstance(val, (int, np.integer)):
        return f"{val:,}"
    return str(val)


# ── intent patterns ───────────────────────────────────────────────────────────

PATTERNS = [
    # "how many rows / records"
    (r"\b(how many|count of|number of)\b.*(row|record|entr|line)", "count_rows"),
    # "how many columns"
    (r"\b(how many|number of)\b.*(column|field|attrib)", "count_cols"),
    # "what columns / fields do we have"
    (r"\b(what|which|list|show).*(column|field|header)", "list_cols"),
    # "total / sum of <col>"
    (r"\b(total|sum)\b.*\b(\w[\w\s]*)", "sum_col"),
    # "average / mean of <col>"
    (r"\b(average|avg|mean)\b.*\b(\w[\w\s]*)", "avg_col"),
    # "max / highest / largest <col>"
    (r"\b(max|maximum|highest|largest|biggest|most)\b.*\b(\w[\w\s]*)", "max_col"),
    # "min / lowest / smallest <col>"
    (r"\b(min|minimum|lowest|smallest|least|fewest)\b.*\b(\w[\w\s]*)", "min_col"),
    # "top N <col> by <col>"
    (r"\btop\s*(\d+)\b", "top_n"),
    # "bottom N"
    (r"\bbottom\s*(\d+)\b", "bottom_n"),
    # "unique values in <col>"
    (r"\b(unique|distinct)\b.*\b(\w[\w\s]*)", "unique_col"),
    # "missing / null values"
    (r"\b(missing|null|empty|blank|na\b)", "missing"),
    # "duplicates"
    (r"\b(duplicate|dup)\b", "duplicates"),
    # "describe / summary / statistics"
    (r"\b(describe|summary|statistic|overview|profile)", "describe"),
    # "correlation between"
    (r"\b(correlat|relation)\b", "correlation"),
    # "filter / where / show rows where"
    (r"\b(filter|where|show rows|find rows|rows where)\b", "filter_rows"),
    # "group by"
    (r"\bgroup\s*by\b", "group_by"),
    # "trend / over time"
    (r"\b(trend|over time|by month|by year|by week|by day)\b", "trend"),
    # comparison
    (r"\b(compar|vs\.?|versus|between)\b", "compare"),
]


def _match_intent(query: str) -> str:
    q = query.lower()
    for pattern, intent in PATTERNS:
        if re.search(pattern, q):
            return intent
    return "general"


def _extract_col_from_query(query: str, df: pd.DataFrame) -> str | None:
    """Scan query for column name hints."""
    q = query.lower()
    candidates = []
    for col in df.columns:
        if col.lower() in q or col.lower().replace("_", " ") in q:
            candidates.append(col)
    if candidates:
        # prefer the longest match
        return sorted(candidates, key=len, reverse=True)[0]
    # Try word-level fallback
    words = re.findall(r"[a-z_]+", q)
    for w in words:
        if len(w) < 3:
            continue
        c = _find_col(df, w)
        if c:
            return c
    return None


def _extract_number(query: str) -> int | None:
    m = re.search(r"\b(\d+)\b", query)
    return int(m.group(1)) if m else None


# ── responders ────────────────────────────────────────────────────────────────

def _respond(df: pd.DataFrame, query: str) -> str:
    intent = _match_intent(query)
    q = query.lower()

    if intent == "count_rows":
        return f"📋 There are **{len(df):,}** rows (records) in your dataset."

    if intent == "count_cols":
        return f"📐 Your dataset has **{len(df.columns)}** columns: {', '.join(df.columns.tolist())}."

    if intent == "list_cols":
        cols = df.columns.tolist()
        bullet = "\n".join(f"- `{c}`" for c in cols)
        return f"📋 **Columns ({len(cols)}):**\n{bullet}"

    if intent == "describe":
        num = df.select_dtypes(include=[np.number])
        if num.empty:
            return "ℹ️ No numeric columns to describe."
        desc = num.describe().round(2)
        return "📊 **Statistical Summary:**\n" + desc.to_markdown()

    if intent == "missing":
        miss = df.isnull().sum()
        miss = miss[miss > 0]
        if miss.empty:
            return "✅ No missing values found in the dataset — it's clean!"
        lines = "\n".join(f"- **{c}**: {n} missing ({n/len(df)*100:.1f}%)" for c, n in miss.items())
        return f"⚠️ **Missing values detected:**\n{lines}"

    if intent == "duplicates":
        n = df.duplicated().sum()
        if n == 0:
            return "✅ No duplicate rows found."
        return f"⚠️ Found **{n}** duplicate row(s) in the dataset."

    if intent == "sum_col":
        col = _extract_col_from_query(query, df)
        if col and pd.api.types.is_numeric_dtype(df[col]):
            val = df[col].sum()
            return f"➕ Total **{col}** = **{_fmt(val)}**"
        if col:
            return f"⚠️ Column `{col}` is not numeric."
        # fall back: sum all numerics
        sums = df[_num_cols(df)].sum()
        lines = "\n".join(f"- **{c}**: {_fmt(v)}" for c, v in sums.items())
        return f"➕ **Totals for all numeric columns:**\n{lines}"

    if intent == "avg_col":
        col = _extract_col_from_query(query, df)
        if col and pd.api.types.is_numeric_dtype(df[col]):
            val = df[col].mean()
            return f"📐 Average **{col}** = **{_fmt(val)}**"
        avgs = df[_num_cols(df)].mean()
        lines = "\n".join(f"- **{c}**: {_fmt(v)}" for c, v in avgs.items())
        return f"📐 **Averages for all numeric columns:**\n{lines}"

    if intent == "max_col":
        col = _extract_col_from_query(query, df)
        if col and pd.api.types.is_numeric_dtype(df[col]):
            val = df[col].max()
            idx = df[col].idxmax()
            row_info = df.loc[idx].to_dict()
            return f"🔝 Maximum **{col}** = **{_fmt(val)}**\n\nRow details: {row_info}"
        if col:
            val = df[col].value_counts().idxmax()
            return f"🔝 Most common value in **{col}**: **{val}**"
        return "Please specify a column name, e.g. *'max of revenue'*."

    if intent == "min_col":
        col = _extract_col_from_query(query, df)
        if col and pd.api.types.is_numeric_dtype(df[col]):
            val = df[col].min()
            return f"🔽 Minimum **{col}** = **{_fmt(val)}**"
        return "Please specify a column name, e.g. *'min of price'*."

    if intent == "unique_col":
        col = _extract_col_from_query(query, df)
        if col:
            vals = df[col].dropna().unique()
            if len(vals) <= 30:
                return f"🏷️ **Unique values in `{col}`** ({len(vals)}):\n" + ", ".join(str(v) for v in sorted(vals))
            return f"🏷️ Column `{col}` has **{len(vals):,}** unique values. Sample: {', '.join(str(v) for v in vals[:10])}..."
        return "Please specify a column, e.g. *'unique values in region'*."

    if intent == "top_n":
        n = _extract_number(query) or 5
        sort_col = _extract_col_from_query(query, df)
        if sort_col and pd.api.types.is_numeric_dtype(df[sort_col]):
            top = df.nlargest(n, sort_col)
            return f"🏆 **Top {n} rows by `{sort_col}`:**\n" + top.to_markdown(index=False)
        return f"🏆 **Top {n} rows:**\n" + df.head(n).to_markdown(index=False)

    if intent == "bottom_n":
        n = _extract_number(query) or 5
        sort_col = _extract_col_from_query(query, df)
        if sort_col and pd.api.types.is_numeric_dtype(df[sort_col]):
            bot = df.nsmallest(n, sort_col)
            return f"🔻 **Bottom {n} rows by `{sort_col}`:**\n" + bot.to_markdown(index=False)
        return f"🔻 **Last {n} rows:**\n" + df.tail(n).to_markdown(index=False)

    if intent == "correlation":
        num = df.select_dtypes(include=[np.number])
        if len(num.columns) < 2:
            return "ℹ️ Need at least 2 numeric columns to compute correlations."
        corr = num.corr().round(2)
        return "🔗 **Correlation Matrix:**\n" + corr.to_markdown()

    if intent == "group_by":
        # Try to find group col and agg col
        cat = _cat_cols(df)
        num = _num_cols(df)
        if not cat or not num:
            return "ℹ️ Need categorical and numeric columns to group."
        group_col = cat[0]
        agg_col = num[0]
        # Try to extract from query
        for c in cat:
            if c.lower() in q or c.lower().replace("_", " ") in q:
                group_col = c
                break
        for c in num:
            if c.lower() in q or c.lower().replace("_", " ") in q:
                agg_col = c
                break
        result = df.groupby(group_col)[agg_col].agg(["sum", "mean", "count"]).round(2)
        result.columns = ["Total", "Average", "Count"]
        result = result.sort_values("Total", ascending=False)
        return f"📊 **`{agg_col}` grouped by `{group_col}`:**\n" + result.to_markdown()

    if intent == "trend":
        date_c = _date_cols(df)
        num = _num_cols(df)
        if not date_c or not num:
            return "ℹ️ Need a date column and a numeric column to show trends."
        dc = date_c[0]
        nc = num[0]
        tmp = df.copy()
        tmp["_month"] = tmp[dc].dt.to_period("M").astype(str)
        result = tmp.groupby("_month")[nc].sum().reset_index()
        result.columns = ["Period", nc]
        return f"📈 **`{nc}` trend by month:**\n" + result.to_markdown(index=False)

    if intent == "filter_rows":
        # Simple: find col, find value
        cat = _cat_cols(df)
        for c in cat:
            if c.lower() in q:
                # find quoted or word after "="
                m = re.search(r"[='\"]?\s*([a-zA-Z][\w\s]+)", q.split(c.lower())[-1])
                if m:
                    val_hint = m.group(1).strip().strip("\"'")
                    # fuzzy match value
                    uniq = df[c].dropna().unique()
                    for v in uniq:
                        if val_hint.lower() in str(v).lower():
                            filtered = df[df[c] == v]
                            return (f"🔍 **Rows where `{c}` = `{v}`** ({len(filtered):,} rows):\n"
                                    + filtered.head(20).to_markdown(index=False))
        return "🔍 Filtering: please specify column and value, e.g. *'show rows where region is East'*."

    if intent == "compare":
        cat = _cat_cols(df)
        num = _num_cols(df)
        if cat and num:
            g = df.groupby(cat[0])[num[0]].agg(["sum", "mean"]).round(2)
            g.columns = ["Total", "Average"]
            g = g.sort_values("Total", ascending=False)
            return f"⚖️ **`{num[0]}` comparison by `{cat[0]}`:**\n" + g.to_markdown()

    # ── fallback: general keyword search ─────────────────────────────────────
    col = _extract_col_from_query(query, df)
    if col:
        if pd.api.types.is_numeric_dtype(df[col]):
            s = df[col].describe().round(2)
            return (f"📊 **Stats for `{col}`:**\n"
                    f"- Count: {_fmt(s['count'])}\n"
                    f"- Mean: {_fmt(s['mean'])}\n"
                    f"- Min: {_fmt(s['min'])}\n"
                    f"- Max: {_fmt(s['max'])}\n"
                    f"- Std Dev: {_fmt(s['std'])}")
        else:
            vc = df[col].value_counts().head(10)
            lines = "\n".join(f"- **{v}**: {c:,}" for v, c in vc.items())
            return f"📋 **Top values in `{col}`:**\n{lines}"

    return (
        "🤔 I couldn't find a specific answer. Try asking:\n"
        "- *'Total revenue'*\n"
        "- *'Top 5 by sales'*\n"
        "- *'Show missing values'*\n"
        "- *'Average price by region'*\n"
        "- *'Unique values in category'*"
    )


def answer_query(df: pd.DataFrame, query: str) -> str:
    try:
        return _respond(df, query)
    except Exception as e:
        return f"⚠️ Couldn't process your query: {e}. Please try rephrasing."
