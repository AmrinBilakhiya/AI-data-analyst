import streamlit as st
from utils.nlq_engine import answer_query

EXAMPLE_QUESTIONS = [
    "How many rows are in this dataset?",
    "What columns do we have?",
    "Show me the total revenue",
    "What is the average sales amount?",
    "Find missing values",
    "Show top 5 by revenue",
    "Group by region and show totals",
    "Are there any duplicates?",
    "What are the unique categories?",
    "Show me the maximum value",
]


def render():
    st.markdown("""
    <div class="page-header">
        <h1>💬 Ask Your Data</h1>
        <p class="page-sub">Ask any question in plain English — no SQL or code needed.</p>
    </div>
    """, unsafe_allow_html=True)

    df = st.session_state.get("df_clean") or st.session_state.get("df")
    if df is None:
        st.warning("⚠️ Please upload a file first.")
        if st.button("Go to Upload"):
            st.session_state.active_tab = "upload"
            st.rerun()
        return

    # Example questions
    st.markdown("#### 💡 Example Questions — click to ask:")
    cols = st.columns(5)
    for i, q in enumerate(EXAMPLE_QUESTIONS):
        with cols[i % 5]:
            if st.button(q, key=f"eq_{i}", use_container_width=True):
                _add_and_answer(df, q)
                st.rerun()

    st.markdown("---")

    # Chat history
    history = st.session_state.get("chat_history", [])
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            st.markdown(f'<div class="chat-bubble user-bubble">🧑 {content}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble bot-bubble">🤖 {content}</div>',
                        unsafe_allow_html=True)

    # Input
    st.markdown("---")
    with st.form(key="chat_form", clear_on_submit=True):
        c1, c2 = st.columns([6, 1])
        user_input = c1.text_input(
            "Your question:",
            placeholder="e.g. What is the total revenue by region?",
            label_visibility="collapsed",
        )
        submitted = c2.form_submit_button("Ask →", type="primary", use_container_width=True)

    if submitted and user_input.strip():
        _add_and_answer(df, user_input.strip())
        st.rerun()

    if history:
        if st.button("🗑️  Clear Chat History", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()


def _add_and_answer(df, question: str):
    history = st.session_state.get("chat_history", [])
    history.append({"role": "user", "content": question})
    answer = answer_query(df, question)
    history.append({"role": "bot", "content": answer})
    st.session_state.chat_history = history
