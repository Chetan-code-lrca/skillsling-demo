import streamlit as st
import ollama
import time
import json
import os
import io
from current_facts import get_current_facts
from datetime import datetime
from pypdf import PdfReader

# ==================== CONFIG ====================
AVAILABLE_MODELS = ["llama3.2:3b", "gemma2:2b", "phi3:mini"]

PLACEHOLDERS = {
    "Hindi": "Doubt poocho...",
    "English": "Ask your doubt...",
    "Hinglish": "Doubt poocho yaar...",
    "Tamil": "கேள்வி கேளுங்கள்...",
    "Telugu": "డౌట్ ఏదైనా అడుగు..."
}

LANG_SYSTEM_PROMPT = {
    "Hindi": "MANDATE: RESPOND ONLY IN HINDI DEVANAGARI SCRIPT. Follow NCERT guidelines.",
    "English": "MANDATE: RESPOND ONLY IN ENGLISH. Follow NCERT guidelines.",
    "Hinglish": "MANDATE: RESPOND IN HINGLISH. Follow NCERT guidelines.",
    "Tamil": "MANDATE: RESPOND ONLY IN TAMIL SCRIPT. Follow NCERT guidelines.",
    "Telugu": "MANDATE: RESPOND ONLY IN TELUGU SCRIPT. Follow NCERT guidelines."
}

MODEL_OPTS = {"temperature": 0.3, "num_predict": 1024}
HISTORY_FILE = "chat_history.json"

st.set_page_config(page_title="SkillSling AI", page_icon="🚀", layout="wide")

# ==================== MODERN DARK UI CSS ====================
st.markdown("""
    <style>
    .stApp { background-color: #0b0d11; color: #e3e3e3; }
    section[data-testid="stSidebar"] { background-color: #111216 !important; border-right: 1px solid #333; }
    
    .stChatMessage { border-radius: 12px; padding: 1.2rem; margin-bottom: 0.5rem; max-width: 850px; margin-left: auto; margin-right: auto; }
    [data-testid="stChatMessageUser"] { background-color: #1e1f23 !important; border: 1px solid #333; }
    
    .perf-badge {
        background: linear-gradient(90deg, #ed1c24 0%, #000000 100%);
        padding: 5px 12px; border-radius: 20px; font-size: 0.7rem; font-weight: bold; color: white;
        text-transform: uppercase; border: 1px solid #ed1c24; display: inline-block; margin-bottom: 10px;
    }
    
    .metric-text { font-size: 0.75rem; opacity: 0.5; font-family: monospace; margin-top: -5px; margin-bottom: 15px; text-align: center;}
    
    header[data-testid="stHeader"] { background-color: rgba(11, 13, 17, 0.9) !important; }
    #MainMenu, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==================== STATE ====================
if "messages" not in st.session_state: st.session_state.messages = []
if "language" not in st.session_state: st.session_state.language = "English"
if "model" not in st.session_state: st.session_state.model = "llama3.2:3b"
if "past_chats" not in st.session_state: st.session_state.past_chats = []
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = f"chat_{int(time.time())}"
if "context_text" not in st.session_state: st.session_state.context_text = ""

def save_history(history):
    try:
        with io.open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except: pass

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("<h2 style='color: #ed1c24 !important; text-align: center;'>SKILLSLING</h2>", unsafe_allow_html=True)
    st.markdown("<div class='perf-badge'>⚡ AMD LOCAL INFERENCE</div>", unsafe_allow_html=True)
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.context_text = ""
        st.session_state.current_chat_id = f"chat_{int(time.time())}"
        st.rerun()

    st.markdown("---")
    st.subheader("📚 Study Material")
    uploaded_file = st.file_uploader("Upload Notes (PDF)", type="pdf")
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        st.session_state.context_text = "\n".join([p.extract_text() for p in reader.pages[:10]])
        st.success("Notes Attached!")

    st.markdown("---")
    st.subheader("Interactive Study")
    if st.button("📝 Test My Knowledge", use_container_width=True):
        if st.session_state.messages:
            st.session_state.messages.append({"role": "user", "content": "Generate a short quiz based on our session."})
            st.rerun()

    st.markdown("---")
    st.subheader("Settings")
    st.session_state.language = st.selectbox("Language", ["English", "Hindi", "Hinglish", "Tamil", "Telugu"], index=["English", "Hindi", "Hinglish", "Tamil", "Telugu"].index(st.session_state.language))
    st.session_state.model = st.selectbox("Model", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model))

# ==================== MAIN CONTENT ====================
if not st.session_state.messages:
    st.markdown("<div style='text-align:center; padding: 50px;'><h1 style='color:#ed1c24;'>SkillSling AI</h1><p>Your local intelligent tutor. Upload notes in the sidebar to start.</p></div>", unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
    if msg["role"] == "assistant" and "perf" in msg:
        st.markdown(f"<div class='metric-text'>Latency: {msg['perf']}s | AMD Optimized</div>", unsafe_allow_html=True)

# ==================== INPUT ====================
prompt = st.chat_input(PLACEHOLDERS.get(st.session_state.language, "Ask anything..."))

if prompt or (st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and len(st.session_state.messages) > 0 and "assistant" not in [m["role"] for m in st.session_state.messages[-1:]]):
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    else:
        prompt = st.session_state.messages[-1]["content"]

    sys_p = LANG_SYSTEM_PROMPT.get(st.session_state.language, LANG_SYSTEM_PROMPT["English"])
    messages = [{"role": "system", "content": sys_p}]
    
    if st.session_state.context_text:
        messages.append({"role": "system", "content": f"CONTEXT: {st.session_state.context_text[:5000]}"})
    
    fact = get_current_facts(prompt)
    if fact: messages.append({"role": "system", "content": f"FACT: {fact}"})
    for m in st.session_state.messages: messages.append(m)

    with st.chat_message("assistant"):
        p_hold = st.empty()
        full_res = ""
        start_t = time.time()
        try:
            stream = ollama.chat(model=st.session_state.model, messages=messages, stream=True, options=MODEL_OPTS)
            for chunk in stream:
                if 'message' in chunk:
                    full_res += chunk['message']['content']
                    p_hold.markdown(full_res + "▌")
            duration = round(time.time() - start_t, 2)
            p_hold.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res, "perf": duration})
            
            chat_entry = {"id": st.session_state.current_chat_id, "messages": st.session_state.messages, "preview": st.session_state.messages[0]["content"][:40]}
            if not any(c.get("id") == chat_entry["id"] for c in st.session_state.past_chats):
                st.session_state.past_chats.append(chat_entry)
            save_history(st.session_state.past_chats)
        except Exception as e:
            st.error(f"Inference Error: {str(e)}")
