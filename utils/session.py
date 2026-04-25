import streamlit as st

def init_session():
    defaults = {
        "df": None,
        "df_clean": None,
        "filename": None,
        "chat_history": [],
        "active_tab": "upload",
        "cleaning_report": None,
        "kpis": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
