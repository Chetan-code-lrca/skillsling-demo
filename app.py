import streamlit as st
import ollama
import time
import json
import os
import io
from current_facts import get_current_facts
from datetime import datetime

# ==================== CONFIG ====================
AVAILABLE_MODELS = ["llama3.2:3b", "gemma2:2b", "phi3:mini"]

PLACEHOLDERS = {
    "Hindi": "Doubt poocho... (Hindi)",
    "English": "Ask your doubt... (English)",
    "Hinglish": "Doubt poocho yaar... (Hinglish)",
    "Tamil": "கேள்வி கேளுங்கள்... (Tamil)",
    "Telugu": "డౌట్ ఏదైనా అడుగు... (Telugu)"
}

LANG_SYSTEM_PROMPT = {
    "Hindi": "MANDATE: RESPOND ONLY IN HINDI DEVANAGARI SCRIPT. Follow NCERT guidelines.",
    "English": "MANDATE: RESPOND ONLY IN ENGLISH. Follow NCERT guidelines.",
    "Hinglish": "MANDATE: RESPOND IN HINGLISH (HINDI+ENGLISH MIX). Follow NCERT guidelines.",
    "Tamil": "MANDATE: RESPOND ONLY IN TAMIL SCRIPT. Follow NCERT guidelines.",
    "Telugu": "MANDATE: RESPOND ONLY IN TELUGU SCRIPT. Follow NCERT guidelines."
}

MODEL_OPTS = {"temperature": 0.3, "num_predict": 1024}
HISTORY_FILE = "chat_history.json"

st.set_page_config(page_title="SkillSling AI", page_icon="🚀", layout="wide")

# ==================== CSS ====================
st.markdown("""
    <style>
    .stApp { background-color: #0b0d11; color: #e3e3e3; }
    section[data-testid="stSidebar"] { background-color: #111216 !important; border-right: 1px solid #333; }
    .stChatMessage { border-radius: 12px; padding: 1.2rem; margin-bottom: 0rem; max-width: 850px; margin-left: auto; margin-right: auto; }
    [data-testid="stChatMessageUser"] { background-color: #1e1f23 !important; border: 1px solid #333; }
    .perf-badge {
        background: linear-gradient(90deg, #ed1c24 0%, #000000 100%);
        padding: 5px 12px; border-radius: 20px; font-size: 0.7rem; font-weight: bold; color: white;
        text-transform: uppercase; border: 1px solid #ed1c24; display: inline-block; margin-bottom: 10px;
    }
    .metric-text { font-size: 0.8rem; opacity: 0.5; font-family: monospace; margin-top: -10px; margin-bottom: 10px;}
    header[data-testid="stHeader"] { background-color: rgba(11, 13, 17, 0.9) !important; }
    #MainMenu, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==================== STATE & HISTORY ====================
if "messages" not in st.session_state: st.session_state.messages = []
if "language" not in st.session_state: st.session_state.language = "English"
if "model" not in st.session_state: st.session_state.model = "llama3.2:3b"
if "past_chats" not in st.session_state: st.session_state.past_chats = []
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = f"chat_{int(time.time())}"
if "edit_index" not in st.session_state: st.session_state.edit_index = None

def save_history(history):
    try:
        with io.open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except: pass

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with io.open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

if "history_loaded" not in st.session_state:
    st.session_state.past_chats = load_history()
    st.session_state.history_loaded = True

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("<h2 style='color: #ed1c24 !important; text-align: center;'>SKILLSLING</h2>", unsafe_allow_html=True)
    st.markdown("<div class='perf-badge'>⚡ AMD LOCAL INFERENCE</div>", unsafe_allow_html=True)
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.edit_index = None
        st.session_state.current_chat_id = f"chat_{int(time.time())}"
        st.rerun()

    st.markdown("---")
    st.subheader("Interactive Study")
    if st.button("📝 Test My Knowledge", use_container_width=True):
        if st.session_state.messages:
            st.session_state.messages.append({"role": "user", "content": "Generate a short quiz based on our study session in my current language."})
            st.rerun()
        else:
            st.warning("Chat first to generate a quiz!")

    st.markdown("---")
    st.subheader("Settings")
    new_lang = st.selectbox("Language", ["English", "Hindi", "Hinglish", "Tamil", "Telugu"], index=["English", "Hindi", "Hinglish", "Tamil", "Telugu"].index(st.session_state.language))
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.session_state.messages = []
        st.rerun()

    st.session_state.model = st.selectbox("Model", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model))

    st.markdown("---")
    st.subheader("History")
    if st.session_state.past_chats:
        for idx, chat in enumerate(reversed(st.session_state.past_chats[-10:])):
            real_idx = len(st.session_state.past_chats) - 1 - idx
            preview = (chat.get("preview") or "Session")[:20] + "..."
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"💬 {preview}", key=f"hist_{real_idx}", use_container_width=True):
                    st.session_state.messages = chat.get("messages", [])
                    st.session_state.current_chat_id = chat.get("id")
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_hist_{real_idx}"):
                    st.session_state.past_chats.pop(real_idx)
                    save_history(st.session_state.past_chats)
                    st.rerun()
    else:
        st.caption("No history found")

# ==================== MAIN DISPLAY ====================
if st.session_state.edit_index is not None:
    st.info("✏️ Edit Question Mode")
    edit_val = st.session_state.messages[st.session_state.edit_index]["content"]
    new_text = st.text_area("Update your question:", value=edit_val, height=100)
    c1, c2 = st.columns([1, 5])
    if c1.button("Update"):
        st.session_state.messages = st.session_state.messages[:st.session_state.edit_index]
        st.session_state.messages.append({"role": "user", "content": new_text})
        st.session_state.edit_index = None
        st.rerun()
    if c2.button("Cancel"):
        st.session_state.edit_index = None
        st.rerun()
    st.stop()

if not st.session_state.messages:
    st.markdown("<div style='text-align:center; padding: 50px;'><h1 style='color:#ed1c24;'>SkillSling AI</h1><p>Offline Tutoring for AMD Slingshot 2026</p></div>", unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
    if msg["role"] == "user":
        c1, c2, _ = st.columns([0.05, 0.05, 0.9])
        if c1.button("🗑️", key=f"d_{i}"):
            st.session_state.messages = st.session_state.messages[:i]
            st.rerun()
        if c2.button("✏️", key=f"e_{i}"):
            st.session_state.edit_index = i
            st.rerun()
    if "perf" in msg and msg["role"] == "assistant":
        st.markdown(f"<div class='metric-text' style='max-width:850px; margin:auto; padding-left:1.2rem;'>Latency: {msg['perf']}s</div>", unsafe_allow_html=True)

# ==================== INFERENCE ====================
prompt = st.chat_input(PLACEHOLDERS.get(st.session_state.language, "Ask anything..."))

if prompt or (st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.edit_index is None):
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    else:
        prompt = st.session_state.messages[-1]["content"]

    sys_p = LANG_SYSTEM_PROMPT.get(st.session_state.language, LANG_SYSTEM_PROMPT["English"])
    messages = [{"role": "system", "content": sys_p}]
    fact = get_current_facts(prompt)
    if fact: messages.append({"role": "system", "content": f"FACT: {fact}"})
    for m in st.session_state.messages: messages.append(m)

    with st.chat_message("assistant"):
        p_hold = st.empty()
        full_res = ""
        start_t = time.time()
        try:
            with st.spinner("Processing..."):
                stream = ollama.chat(model=st.session_state.model, messages=messages, stream=True, options=MODEL_OPTS)
                for chunk in stream:
                    if 'message' in chunk:
                        full_res += chunk['message']['content']
                        p_hold.markdown(full_res + "▌")
                duration = round(time.time() - start_t, 2)
                p_hold.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res, "perf": duration})
                
                chat_entry = {"id": st.session_state.current_chat_id, "messages": st.session_state.messages, "preview": st.session_state.messages[0]["content"][:40]}
                found = False
                for idx, c in enumerate(st.session_state.past_chats):
                    if c.get("id") == chat_entry["id"]:
                        st.session_state.past_chats[idx] = chat_entry
                        found = True
                        break
                if not found: st.session_state.past_chats.append(chat_entry)
                save_history(st.session_state.past_chats)
        except Exception as e:
            st.error(f"Inference Error: {str(e)}")
