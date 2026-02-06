import streamlit as st
from ollama import Client
import json
from datetime import datetime

# ────────────────────────────────────────────────
# Page config + custom CSS for "real" look
# ────────────────────────────────────────────────
st.set_page_config(page_title="SkillSling", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        color: white;
    }
    .stTextInput > div > div > input {
        background-color: rgba(255,255,255,0.1);
        color: white;
        border: 1px solid #4a90e2;
    }
    .stButton > button {
        background-color: #4a90e2;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px;
    }
    .stButton > button:hover {
        background-color: #357abd;
    }
    .chat-user {
        background-color: #4a90e2;
        color: white;
        border-radius: 15px 15px 0 15px;
        padding: 10px;
        margin: 10px;
        max-width: 70%;
        align-self: flex-end;
    }
    .chat-ai {
        background-color: #2ecc71;
        color: white;
        border-radius: 15px 15px 15px 0;
        padding: 10px;
        margin: 10px;
        max-width: 70%;
        align-self: flex-start;
    }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Login / Register
# ────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.users = {"guest": "123"}  # test user

if not st.session_state.logged_in:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://images.unsplash.com/photo-1523050854058-8df90110c9f1?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", use_column_width=True)
    with col2:
        st.title("Welcome to SkillSling")
        st.markdown("Your offline AI tutor — private & personal chats saved locally.")

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True):
                if username in st.session_state.users and st.session_state.users[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        with tab2:
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            if st.button("Register", use_container_width=True):
                if new_user and new_pass:
                    st.session_state.users[new_user] = new_pass
                    st.session_state.logged_in = True
                    st.session_state.username = new_user
                    st.rerun()
                else:
                    st.error("Fill both fields")

    st.stop()

# ────────────────────────────────────────────────
# Main App after login
# ────────────────────────────────────────────────
st.title(f"SkillSling – Hi, {st.session_state.username}! 🧠")
st.markdown("Your personal offline tutor — chats saved just for you.")

client = Client()

# Load user's chat history (per user key)
user_key = f"chat_{st.session_state.username}"
if user_key not in st.session_state:
    st.session_state[user_key] = []

messages = st.session_state[user_key]

# Logout + Clear
col1, col2, col3 = st.columns([6, 2, 2])
with col2:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
with col3:
    if st.button("Clear History"):
        st.session_state[user_key] = []
        messages = []
        st.rerun()

# Show saved chats list
if messages:
    st.subheader("Your Saved Chats")
    for idx, msg in enumerate(messages):
        if msg["role"] == "user":
            st.markdown(f"**{msg['content'][:50]}...** (saved {datetime.now().strftime('%b %d')})")
            if st.button("Load this chat", key=f"load_{idx}"):
                # Simple reload logic - for demo
                st.session_state.messages = messages[:idx+1]
                st.rerun()

# Chat area
for message in messages:
    avatar = "🧑‍🎓" if message["role"] == "user" else "🧠"
    css_class = "chat-user" if message["role"] == "user" else "chat-ai"
    st.markdown(f"<div class='{css_class}'>{message['content']}</div>", unsafe_allow_html=True)

# Input
if prompt := st.chat_input("Ask your doubt..."):
    messages.append({"role": "user", "content": prompt})
    st.markdown(f"<div class='chat-user'>{prompt}</div>", unsafe_allow_html=True)

    system_prompt = {
        "role": "system",
        "content": "You are a patient teacher for Indian students. Reply ONLY in user's language. Short answers (80–150 words). Bullet points for lists. No repetition. End with quick check question."
    }

    full_messages = [system_prompt] + messages

    with st.chat_message("assistant", avatar="🧠"):
        message_placeholder = st.empty()
        full_response = ""
        stream_response = client.chat(
            model='gemma2:9b',
            messages=full_messages,
            stream=True,
            options={"temperature": 0.65, "top_p": 0.85, "repeat_penalty": 1.2}
        )

        for chunk in stream_response:
            content = chunk['message']['content']
            full_response += content
            message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)

    messages.append({"role": "assistant", "content": full_response})
    st.session_state[user_key] = messages
