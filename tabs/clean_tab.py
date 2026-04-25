import streamlit as st
import pandas as pd
import io
from utils.cleaner import clean_dataframe, detect_outliers


def render():
    st.markdown("""
    <div class="page-header">
        <h1>🧹 Clean Your Data</h1>
        <p class="page-sub">Automatically fix common data quality issues — missing values, duplicates, inconsistent formats and more.</p>
    </div>
    """, unsafe_allow_html=True)

    df = st.session_state.get("df")
    if df is None:
        st.warning("⚠️ Please upload a file first.")
        if st.button("Go to Upload"):
            st.session_state.active_tab = "upload"
            st.rerun()
        return

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📋 Raw Data Profile")

        total_cells = df.shape[0] * df.shape[1]
        miss_cells = df.isnull().sum().sum()
        dup_rows = df.duplicated().sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Rows", f"{len(df):,}")
        m2.metric("Missing Cells", f"{miss_cells:,}")
        m3.metric("Duplicate Rows", f"{dup_rows:,}")

        st.markdown("**Column Types:**")
        dtype_df = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str).values,
            "Missing": df.isnull().sum().values,
            "Unique": [df[c].nunique() for c in df.columns],
        })
        st.dataframe(dtype_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### ⚡ Auto-Clean Actions")
        st.markdown("""
        The cleaner will automatically:
        - ✅ Strip column name whitespace
        - ✅ Remove fully empty rows/columns
        - ✅ Drop exact duplicate rows
        - ✅ Standardize date formats
        - ✅ Convert currency strings to numbers
        - ✅ Fix inconsistent text casing
        - ✅ Trim leading/trailing spaces
        - ✅ Convert text-encoded numbers
        """)

        if st.button("🧹  Run Auto-Clean", type="primary", use_container_width=True):
            with st.spinner("Cleaning your data..."):
                df_clean, report = clean_dataframe(df)
                st.session_state.df_clean = df_clean
                st.session_state.cleaning_report = report

            st.success("✅ Cleaning complete!")
        st.markdown('</div>', unsafe_allow_html=True)

    # Show results after cleaning
    if st.session_state.get("cleaning_report"):
        st.markdown("---")
        st.markdown("### 📝 Cleaning Report")
        st.markdown('<div class="card report-card">', unsafe_allow_html=True)
        for line in st.session_state.cleaning_report:
            st.markdown(line)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get("df_clean") is not None:
        df_c = st.session_state.df_clean
        st.markdown("---")
        st.markdown("### ✨ Cleaned Data Preview")
        st.dataframe(df_c.head(20), use_container_width=True)

        # Outlier report
        st.markdown("---")
        st.markdown("### 🚨 Outlier Detection")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        outlier_df = detect_outliers(df_c)
        if outlier_df.empty:
            st.success("✅ No statistical outliers detected (IQR method).")
        else:
            st.warning(f"⚠️ Found outliers in **{len(outlier_df)}** column(s):")
            st.dataframe(outlier_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Download cleaned file
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            csv_bytes = df_c.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️  Download Cleaned CSV",
                data=csv_bytes,
                file_name="cleaned_data.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with c2:
            if st.button("➡️  View KPIs", type="primary", use_container_width=True):
                st.session_state.active_tab = "kpi"
                st.rerun()
