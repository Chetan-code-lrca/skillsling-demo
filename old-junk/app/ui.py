import streamlit as st

def load_ui(username, messages):
    # Header
    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="
                width:42px;height:42px;
                border-radius:50%;
                background:#0288d1;
                color:white;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:20px;
                font-weight:bold;">
                {username[0].upper()}
            </div>
            <h2 style="color:#4fc3f7;margin:0;">
                SkillSling – Hi, {username} 👋
            </h2>
        </div>
    """, unsafe_allow_html=True)
    st.caption("Your offline AI tutor for Tier-2/3 students")
    # Buttons
    col1, col2 = st.columns([8, 2])
    with col1:
        if st.button("🆕 New Conversation"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🧹 Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    # Chat area
    st.markdown("<div style='margin-top:20px;'>", unsafe_allow_html=True)
    for msg in messages:
        is_user = msg["role"] == "user"
        align = "flex-end" if is_user else "flex-start"
        bg = "#0288d1" if is_user else "#455a64"
        color = "white" if is_user else "#e0f7fa"
        st.markdown(f"""
            <div style="display:flex;justify-content:{align};margin-bottom:8px;">
                <div style="
                    max-width:70%;
                    padding:12px 16px;
                    border-radius:16px;
                    background:{bg};
                    color:{color};">
                    {msg['content']}
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    # Input box
    prompt = st.chat_input("Ask your doubt (English / Hindi / Hinglish)…")
    return prompt