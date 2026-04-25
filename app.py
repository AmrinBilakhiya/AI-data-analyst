import streamlit as st

st.set_page_config(
    page_title="AI-Auto Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open("styles/main.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from tabs import upload_tab, clean_tab, kpi_tab, dashboard_tab, chat_tab
from utils.session import init_session

init_session()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <span class="brand-icon">🔬</span>
        <span class="brand-name">DataSense AI</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if st.session_state.get("df") is not None:
        rows = len(st.session_state.df)
        cols = len(st.session_state.df.columns)
        fname = st.session_state.get("filename", "file")
        st.markdown(f"""
        <div class="file-badge">
            <div class="file-badge-name">📄 {fname}</div>
            <div class="file-badge-meta">{rows:,} rows · {cols} columns</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

    st.markdown("""
    <div class="sidebar-nav-label">NAVIGATION</div>
    """, unsafe_allow_html=True)

    tabs_meta = [
        ("📤", "Upload",    "upload"),
        ("🧹", "Clean",     "clean"),
        ("📊", "KPIs",      "kpi"),
        ("📈", "Dashboard", "dashboard"),
        ("💬", "Ask Data",  "chat"),
    ]

    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "upload"

    for icon, label, key in tabs_meta:
        active_cls = "nav-btn-active" if st.session_state.active_tab == key else ""
        if st.button(f"{icon}  {label}", key=f"nav_{key}",
                     use_container_width=True,
                     type="primary" if st.session_state.active_tab == key else "secondary"):
            st.session_state.active_tab = key
            st.rerun()

    st.markdown("---")
    st.markdown("""
    <div class="sidebar-footer">
        Built for non-tech users <br>
        <small>No API key needed</small>
    </div>
    """, unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────────────────
tab = st.session_state.active_tab

if tab == "upload":
    upload_tab.render()
elif tab == "clean":
    clean_tab.render()
elif tab == "kpi":
    kpi_tab.render()
elif tab == "dashboard":
    dashboard_tab.render()
elif tab == "chat":
    chat_tab.render()
