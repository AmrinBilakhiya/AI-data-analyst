import pandas as pd
import numpy as np
import re
from datetime import datetime


def _try_parse_dates(series: pd.Series) -> pd.Series:
    """Attempt to parse a series as dates using multiple formats."""
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y",
        "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y",
        "%d %b %Y", "%b %d %Y", "%B %d %Y",
        "%d-%b-%Y", "%b-%d-%Y",
    ]
    for fmt in formats:
        try:
            parsed = pd.to_datetime(series, format=fmt, errors="coerce")
            if parsed.notna().sum() / max(len(series), 1) > 0.6:
                return parsed
        except Exception:
            pass
    parsed = pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
    return parsed


def _clean_currency(val):
    """Strip currency symbols and convert to float."""
    if pd.isna(val):
        return np.nan
    s = str(val).replace(",", "").strip()
    s = re.sub(r"[^\d.\-]", "", s)
    try:
        return float(s)
    except ValueError:
        return np.nan


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Clean a dataframe and return (cleaned_df, report_lines).
    """
    df = df.copy()
    report = []

    # 1. Strip column name whitespace
    original_cols = list(df.columns)
    df.columns = [c.strip() for c in df.columns]
    changed = [o for o, n in zip(original_cols, df.columns) if o != n]
    if changed:
        report.append(f"✅ Stripped whitespace from {len(changed)} column name(s).")

    # 2. Drop completely empty rows / columns
    before_r, before_c = df.shape
    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)
    after_r, after_c = df.shape
    if before_r != after_r:
        report.append(f"✅ Removed {before_r - after_r} fully empty row(s).")
    if before_c != after_c:
        report.append(f"✅ Removed {before_c - after_c} fully empty column(s).")

    # 3. Duplicate rows
    dups = df.duplicated().sum()
    if dups > 0:
        df.drop_duplicates(inplace=True)
        report.append(f"✅ Removed {dups} duplicate row(s).")

    for col in df.columns:
        series = df[col]
        dtype = series.dtype

        # 4. String columns: strip, fix casing
        if dtype == object:
            stripped = series.str.strip() if hasattr(series, "str") else series
            if (stripped != series).any():
                df[col] = stripped
                report.append(f"✅ Stripped leading/trailing spaces in '{col}'.")
                series = df[col]

            # Detect currency columns
            sample = series.dropna().head(50).astype(str)
            currency_like = sample.str.contains(r"^[\$£€₹]", regex=True).mean()
            if currency_like > 0.5:
                df[col] = series.apply(_clean_currency)
                report.append(f"✅ Converted currency strings in '{col}' to numeric.")
                continue

            # Detect date columns
            date_parsed = _try_parse_dates(series)
            if date_parsed.notna().sum() / max(len(series), 1) > 0.6:
                df[col] = date_parsed
                report.append(f"✅ Standardized mixed date formats in '{col}'.")
                continue

            # Detect low-cardinality categorical → title case
            nuniq = series.nunique()
            if nuniq <= 50 and nuniq < len(series) * 0.5:
                titled = series.str.title() if hasattr(series, "str") else series
                if (titled != series).any():
                    df[col] = titled
                    report.append(f"✅ Standardized casing in categorical column '{col}'.")

        # 5. Numeric columns: coerce if stored as object
        if dtype == object:
            coerced = pd.to_numeric(df[col], errors="coerce")
            if coerced.notna().sum() / max(len(df[col]), 1) > 0.8:
                df[col] = coerced
                report.append(f"✅ Converted text-encoded numbers in '{col}' to numeric.")

    # 6. Report missing values
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        miss_str = ", ".join(f"'{c}' ({n})" for c, n in missing.items())
        report.append(f"⚠️  Missing values remain in: {miss_str}. Consider filling or dropping as needed.")

    if not report:
        report.append("✅ Data looks clean — no major issues found.")

    return df, report


def detect_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a summary DataFrame of numeric outliers (IQR method).
    """
    records = []
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        s = df[col].dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        out_mask = (s < lower) | (s > upper)
        count = out_mask.sum()
        if count > 0:
            records.append({
                "Column": col,
                "Outlier Count": count,
                "Lower Fence": round(lower, 2),
                "Upper Fence": round(upper, 2),
                "Min Outlier": round(s[out_mask].min(), 2),
                "Max Outlier": round(s[out_mask].max(), 2),
            })
    if records:
        return pd.DataFrame(records)
    return pd.DataFrame(columns=["Column", "Outlier Count", "Lower Fence", "Upper Fence"])
