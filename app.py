import streamlit as st
from ollama import Client
import json

# ────────────────────────────────────────────────
# Page config
# ────────────────────────────────────────────────
st.set_page_config(page_title="SkillSling", page_icon="🧠", layout="wide")

# ────────────────────────────────────────────────
# Local user management (stored in session_state + localStorage)
# ────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

# Load saved users from localStorage (simulated via session_state for simplicity)
if "users" not in st.session_state:
    st.session_state.users = {"guest": "123"}  # default test user

# ────────────────────────────────────────────────
# Login Page
# ────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.title("SkillSling – Login")
    st.markdown("Enter your username and password to save your chat history.")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True):
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Wrong username or password. Try 'guest' / '123' (or register below).")

    with col2:
        if st.button("Register", use_container_width=True):
            if username and password:
                st.session_state.users[username] = password
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Registered & logged in as {username}!")
                st.rerun()
            else:
                st.error("Enter username and password to register.")

    st.stop()  # Stop here if not logged in

# ────────────────────────────────────────────────
# Logout button (top right)
# ────────────────────────────────────────────────
col1, col2 = st.columns([9, 1])
with col2:
    if st.button("Logout", key="logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

# ────────────────────────────────────────────────
# Main App (after login)
# ────────────────────────────────────────────────
st.title(f"SkillSling – Your Offline AI Tutor ({st.session_state.username})")
st.markdown("Ask doubts in Hindi or English. 100% local — chats saved for you! 🚀")

# Connect to Ollama
@st.cache_resource
def get_ollama_client():
    try:
        return Client()
    except:
        st.error("Ollama not running. Start Ollama and load gemma2:9b.")
        st.stop()

client = get_ollama_client()

# Load saved chat history for this user from localStorage (via session_state simulation)
user_key = f"chat_{st.session_state.username}"
if user_key not in st.session_state:
    # Try to load from browser localStorage (Streamlit doesn't have direct access, so simulate)
    st.session_state[user_key] = []

messages = st.session_state[user_key]

# Clear chat button
if st.button("Clear My Chat History", use_container_width=True):
    st.session_state[user_key] = []
    messages = []
    st.rerun()

# Display chat history
for message in messages:
    avatar = "🧑‍🎓" if message["role"] == "user" else "🧠"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Type your doubt..."):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)

    # Strong system prompt
    system_prompt = {
        "role": "system",
        "content": """You are a patient teacher for Indian students.
Reply ONLY in the user's language (Telugu, Hindi or English).
Keep answers SHORT (80–150 words), accurate, structured.
Use bullet points for lists/formulas.
NEVER repeat anything.
Use simple words.
End with one quick check question like "అర్థమైందా?" or "Samajh aaya?"."""
    }

    full_messages = [system_prompt] + messages

    with st.chat_message("assistant", avatar="🧠"):
        message_placeholder = st.empty()
        full_response = ""

        stream_response = client.chat(
            model='gemma2:9b',  # or 'llama3.1:8b' if you pulled it
            messages=full_messages,
            stream=True,
            options={
                "temperature": 0.65,
                "top_p": 0.85,
                "repeat_penalty": 1.2
            }
        )

        for chunk in stream_response:
            if 'message' in chunk and 'content' in chunk['message']:
                content = chunk['message']['content']
                full_response += content
                message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)

    # Save new message to user's history
    messages.append({"role": "assistant", "content": full_response})
    st.session_state[user_key] = messages  # persist in session
