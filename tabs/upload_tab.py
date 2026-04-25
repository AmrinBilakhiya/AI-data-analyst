import streamlit as st
import pandas as pd
import io


def render():
    st.markdown("""
    <div class="page-header">
        <h1>📤 Upload Your Data</h1>
        <p class="page-sub">Upload a CSV or Excel file to get started — no coding needed.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Drop your file here",
            type=["csv", "xlsx", "xls"],
            label_visibility="collapsed",
        )

        if uploaded is not None:
            try:
                if uploaded.name.endswith(".csv"):
                    # Try different encodings
                    for enc in ["utf-8", "latin-1", "cp1252"]:
                        try:
                            df = pd.read_csv(uploaded, encoding=enc)
                            break
                        except UnicodeDecodeError:
                            uploaded.seek(0)
                else:
                    df = pd.read_excel(uploaded)

                st.session_state.df = df
                st.session_state.df_clean = None
                st.session_state.filename = uploaded.name
                st.session_state.cleaning_report = None
                st.session_state.kpis = None

                st.success(f"✅ Loaded **{uploaded.name}** successfully!")

                st.markdown("**Preview (first 5 rows):**")
                st.dataframe(df.head(), use_container_width=True)

                # Quick stats
                st.markdown("---")
                m1, m2, m3 = st.columns(3)
                m1.metric("Rows", f"{len(df):,}")
                m2.metric("Columns", f"{len(df.columns)}")
                m3.metric("Missing cells", f"{df.isnull().sum().sum():,}")

            except Exception as e:
                st.error(f"❌ Could not read file: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card info-card">
            <h3>🚀 What happens next?</h3>
            <div class="step-list">
                <div class="step-item">
                    <span class="step-num">1</span>
                    <span><b>Clean</b> — Auto-fix dates, casing, duplicates & more</span>
                </div>
                <div class="step-item">
                    <span class="step-num">2</span>
                    <span><b>KPIs</b> — See your key numbers at a glance</span>
                </div>
                <div class="step-item">
                    <span class="step-num">3</span>
                    <span><b>Dashboard</b> — Beautiful auto-generated charts</span>
                </div>
                <div class="step-item">
                    <span class="step-num">4</span>
                    <span><b>Ask Data</b> — Ask questions in plain English</span>
                </div>
            </div>
            <hr/>
            <h3>📁 Supported formats</h3>
            <p>• CSV (.csv)<br>• Excel (.xlsx, .xls)</p>
            <h3>💡 Tips</h3>
            <p>• First row should be column headers<br>
               • Dates, currency, categories all handled automatically<br>
               • Works with messy, real-world data</p>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.get("df") is not None:
        st.markdown("---")
        if st.button("➡️  Go to Clean & Analyze", type="primary", use_container_width=False):
            st.session_state.active_tab = "clean"
            st.rerun()
