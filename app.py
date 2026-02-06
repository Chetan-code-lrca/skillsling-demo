import streamlit as st
from ollama import Client
from datetime import datetime

# ────────────────────────────────────────────────
# Page config + CSS
# ────────────────────────────────────────────────
st.set_page_config(page_title="SkillSling", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: #e0f7fa; }
    .main-title { font-size: 2.8rem; color: #4fc3f7; text-align: center; margin-bottom: 0.3rem; }
    .subtitle { text-align: center; color: #b3e5fc; margin-bottom: 1.5rem; }
    .greeting { display: flex; align-items: center; gap: 1rem; }
    .avatar { width: 48px; height: 48px; background: #0288d1; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.4rem; }
    .chat-container { display: flex; flex-direction: column; gap: 1rem; padding: 1rem; max-height: 65vh; overflow-y: auto; }
    .chat-message { max-width: 75%; padding: 1rem 1.2rem; border-radius: 18px; line-height: 1.5; font-size: 1.05rem; }
    .user-message { align-self: flex-end; background: #0288d1; color: white; border-bottom-right-radius: 4px; }
    .ai-message { align-self: flex-start; background: #455a64; color: #e0f7fa; border-bottom-left-radius: 4px; }
    .timestamp { font-size: 0.75rem; color: #b0bec5; margin-top: 0.2rem; opacity: 0.8; }
    .stChatInput > div > div > textarea { background: rgba(255,255,255,0.08); color: white; border: 1px solid #4fc3f7; border-radius: 12px; }
    .stButton > button { background: #0288d1; color: white; border: none; border-radius: 10px; padding: 0.6rem 1.2rem; }
    .stButton > button:hover { background: #0277bd; }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Login / Register
# ────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.users = {"guest": "123"}

if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>SkillSling</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Your offline AI tutor — private & saved chats</p>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://images.unsplash.com/photo-1523050854058-8df90110c9f1?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", use_column_width=True)
    with col2:
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
                    if new_user in st.session_state.users:
                        st.error("Username taken")
                    else:
                        st.session_state.users[new_user] = new_pass
                        st.session_state.logged_in = True
                        st.session_state.username = new_user
                        st.rerun()
                else:
                    st.error("Fill both fields")
    st.stop()

# ────────────────────────────────────────────────
# Main App
# ────────────────────────────────────────────────
st.markdown(f"<div class='greeting'><div class='avatar'>{st.session_state.username[0].upper()}</div><h1 class='main-title'>SkillSling – Hi, {st.session_state.username}!</h1></div>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Your personal offline tutor — chats saved just for you</p>", unsafe_allow_html=True)

client = Client()

user_key = f"chat_{st.session_state.username}"
if user_key not in st.session_state:
    st.session_state[user_key] = []

messages = st.session_state[user_key]

col_logout, col_clear = st.columns([8, 2])
with col_logout:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
with col_clear:
    if st.button("Clear History"):
        st.session_state[user_key] = []
        messages = []
        st.rerun()

# Saved chats list
if messages:
    st.subheader("Your Saved Chats")
    for idx, msg in enumerate(messages):
        if msg["role"] == "user":
            preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
            st.markdown(f"**{preview}**")
            if st.button("Load this chat", key=f"load_{idx}"):
                st.session_state.messages = messages[:idx+1]
                st.rerun()

# Chat display
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in messages:
        css_class = "chat-user" if message["role"] == "user" else "chat-ai"
        timestamp = datetime.now().strftime("%b %d, %H:%M")
        st.markdown(f"""
            <div class="chat-message {css_class}">
                {message['content']}
            </div>
            <div class="timestamp">{timestamp}</div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Input
if prompt := st.chat_input("Ask your doubt..."):
    messages.append({"role": "user", "content": prompt})
    with chat_container:
        st.markdown(f"""
            <div class="chat-message chat-user">
                {prompt}
            </div>
            <div class="timestamp">{datetime.now().strftime('%b %d, %H:%M')}</div>
        """, unsafe_allow_html=True)

    system_prompt = {
        "role": "system",
        "content": "You are a patient teacher for Indian students. Reply ONLY in user's language. Short answers (80–150 words). Bullet points for lists. No repetition. End with quick check question."
    }

    full_messages = [system_prompt] + messages

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            full_response = ""
            stream_response = client.chat(
                model='gemma2:9b',
                messages=full_messages,
                stream=True,
                options={"temperature": 0.65, "top_p": 0.85, "repeat_penalty": 1.2}
            )

            placeholder = st.empty()
            for chunk in stream_response:
                content = chunk['message']['content']
                full_response += content
                placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

    messages.append({"role": "assistant", "content": full_response})
    st.session_state[user_key] = messages
    st.rerun()
