import streamlit as st
from ollama import Client
from datetime import datetime
import threading

# Import friend's UI function
from ui import load_ui

# Page config
st.set_page_config(page_title="SkillSling", page_icon="🧠", layout="wide")

# State & Lock
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.users = {"guest": "123"}

if "lock" not in st.session_state:
    st.session_state.lock = threading.Lock()

# Login / Register
if not st.session_state.logged_in:
    st.title("SkillSling – Login")
    st.markdown("Enter username & password to save your chats.")
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
                st.error("Wrong credentials. Try 'guest' / '123' or register.")
    with col2:
        if st.button("Register", use_container_width=True):
            if username and password:
                st.session_state.users[username] = password
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Registered & logged in as {username}!")
                st.rerun()
            else:
                st.error("Fill both fields.")
    st.stop()

# Logout button
col1, col2 = st.columns([9, 1])
with col2:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

# Ollama client with connection test
@st.cache_resource
def get_ollama_client():
    try:
        client = Client()
        # Quick test
        client.chat(model='gemma2:9b', messages=[{"role": "user", "content": "hi"}])
        st.success("Ollama connected successfully!")
        return client
    except Exception as e:
        st.error(f"Ollama connection failed: {str(e)}\n\nFix:\n1. Open Ollama desktop app\n2. Run 'ollama serve' in another terminal\n3. Run 'ollama run gemma2:9b' once\n4. Check http://localhost:11434")
        st.stop()

client = get_ollama_client()

# Load user's chat history
user_key = f"chat_{st.session_state.username}"
if user_key not in st.session_state:
    with st.session_state.lock:
        st.session_state[user_key] = []

messages = st.session_state[user_key]

# Use friend's UI (returns prompt)
prompt = load_ui(st.session_state.username, messages)

# Handle new prompt
if prompt:
    with st.session_state.lock:
        messages.append({"role": "user", "content": prompt})
        st.session_state[user_key] = messages.copy()
    st.rerun()

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
        placeholder = st.empty()
        full_response = ""

        try:
            st.write("DEBUG: Calling Ollama (non-streaming)...")

            response = client.chat(
                model='gemma2:9b',
                messages=full_messages,
                options={
                    "temperature": 0.65,
                    "top_p": 0.85,
                    "repeat_penalty": 1.2
                }
            )

            full_response = response['message']['content']
            placeholder.markdown(full_response)

            with st.session_state.lock:
                messages.append({"role": "assistant", "content": full_response})
                st.session_state[user_key] = messages.copy()

            st.rerun()

        except Exception as e:
            st.error(f"Ollama error: {str(e)}\n\nQuick fix:\n1. Restart Ollama app\n2. Run 'ollama run gemma2:9b' in terminal and test 'hi'\n3. Restart laptop if needed")