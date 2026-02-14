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
    "Hindi": "You are SkillSling AI – friendly tutor for Class 8-12 students.\nजब भी प्रश्न हिंदी में पूछा जाए तो उत्तर 100% हिंदी (देवनागरी लिपि) में दें।\n- सरल और स्पष्ट उत्तर दें\n- गणित के प्रश्नों में चरण दिखाएं\n- प्रोत्साहित करने वाले शब्द प्रयोग करें",
    "English": "You are SkillSling AI – friendly tutor for Class 8-12 students.\nAlways respond ONLY in English.\n- Give simple and clear answers\n- Use tables when needed\n- Show steps for math problems\n- Be encouraging",
    "Hinglish": "You are SkillSling AI – friendly tutor for Class 8-12 students.\nHinglish mein jawaab dein - Hindi + English mix.\n- Simple answers dein\n- Math mein steps dikhayen",
    "Tamil": "You are SkillSling AI – friendly tutor for Class 8-12 students.\nதமிழில் மட்டுமே பதில் கூறவும் - Tamil script only.\n- எளிதான பதில் கூறவும்\n- கணிதத்தில் படிகள் காட்டவும்",
    "Telugu": "You are SkillSling AI – friendly tutor for Class 8-12 students.\nTelugu lo em chestunnavo ani reply ivvu - Telugu script only, no English.\n- Simple ga ela jawab ivvu\n- Maths lo steps peduthu\n- Encourage words use chesuko"
}

MODEL_OPTS = {
    "llama3.2:3b": {"temperature": 0.6, "num_predict": 1024},
    "gemma2:2b": {"temperature": 0.6, "num_predict": 800},
    "phi3:mini": {"temperature": 0.6, "num_predict": 800}
}

HISTORY_FILE = "chat_history.json"

st.set_page_config(page_title="SkillSling AI", page_icon="🚀", layout="wide")

# ==================== ADVANCED UI CSS ====================
st.markdown("""
    <style>
    .stApp { background-color: #0b0d11; color: #e3e3e3; }
    section[data-testid="stSidebar"] { background-color: #111216 !important; border-right: 1px solid #333; }
    
    .perf-badge {
        background: linear-gradient(90deg, #ed1c24 0%, #000000 100%);
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: bold;
        color: white;
        text-transform: uppercase;
        border: 1px solid #ed1c24;
        display: inline-block;
        margin-bottom: 10px;
    }

    .stChatMessage { border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; max-width: 850px; margin-left: auto; margin-right: auto; }
    [data-testid="stChatMessageUser"] { background-color: #1e1f23 !important; border: 1px solid #333; }
    [data-testid="stChatMessageAssistant"] { background-color: transparent !important; }
    .stChatInputContainer { background-color: #0b0d11 !important; border-top: 1px solid #333; padding-bottom: 1rem; }
    textarea { background-color: #1e1f23 !important; color: #e3e3e3 !important; border: 1px solid #444 !important; }
    
    .welcome-card {
        background: linear-gradient(180deg, #1e1f23 0%, #111216 100%);
        border: 1px solid #ed1c24;
        padding: 2.5rem;
        border-radius: 20px;
        text-align: center;
        margin: 5rem auto;
        max-width: 700px;
        box-shadow: 0 10px 30px rgba(237, 28, 36, 0.1);
    }
    
    header[data-testid="stHeader"] { background-color: rgba(11, 13, 17, 0.9) !important; }
    button[kind="header"] { color: white !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if "messages" not in st.session_state: st.session_state.messages = []
if "language" not in st.session_state: st.session_state.language = "English"
if "model" not in st.session_state: st.session_state.model = "llama3.2:3b"
if "past_chats" not in st.session_state: st.session_state.past_chats = []
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = f"chat_{int(time.time())}"

# ==================== HISTORY FUNCTIONS ====================
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with io.open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def save_history(history):
    try:
        with io.open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e: st.error(f"Failed to save history: {e}")

if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = True
    st.session_state.past_chats = load_history()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("<div style='text-align: center;'><h2 style='color: #ed1c24 !important; margin-bottom: 0;'>SKILLSLING AI</h2><p style='font-size: 0.8rem; opacity: 0.6;'>AMD SLINGSHOT 2026</p></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='perf-badge'>⚡ AMD LOCAL INFERENCE</div>", unsafe_allow_html=True)
    
    if st.button("➕ New Session", use_container_width=True):
        if len(st.session_state.messages) > 0:
            chat_entry = {
                "id": st.session_state.current_chat_id,
                "language": st.session_state.language,
                "model": st.session_state.model,
                "messages": st.session_state.messages,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "preview": st.session_state.messages[0]["content"][:40] if st.session_state.messages else "New Session"
            }
            if not any(c.get("id") == chat_entry["id"] for c in st.session_state.past_chats):
                st.session_state.past_chats.append(chat_entry)
            save_history(st.session_state.past_chats)
        st.session_state.current_chat_id = f"chat_{int(time.time())}"
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.subheader("Settings")
    lang_options = ["Hindi", "English", "Hinglish", "Tamil", "Telugu"]
    st.session_state.language = st.selectbox("🌍 Study Language", lang_options, index=lang_options.index(st.session_state.language))
    st.session_state.model = st.selectbox("🤖 Brain Model", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model))

    st.markdown("---")
    st.subheader("Offline History")
    if st.session_state.past_chats:
        for idx, chat in enumerate(reversed(st.session_state.past_chats[-10:])):
            real_idx = len(st.session_state.past_chats) - 1 - idx
            preview = (chat.get("preview") or "Session")[:25] + "..."
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(f"💬 {preview}", key=f"btn_{chat.get('id', real_idx)}", use_container_width=True):
                    st.session_state.current_chat_id = chat.get("id", "")
                    st.session_state.messages = chat.get("messages", [])
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{chat.get('id', real_idx)}"):
                    st.session_state.past_chats.pop(real_idx)
                    save_history(st.session_state.past_chats)
                    st.rerun()

# ==================== MAIN CONTENT ====================
if not st.session_state.messages:
    st.markdown("""
        <div class="welcome-card">
            <h1 style='color: #ed1c24 !important;'>Empowering Students Offline</h1>
            <p style='font-size: 1.1rem;'>Experience the power of local AI in your native language.</p>
            <div style='margin-top: 2rem;'>
                <span style='background: #333; padding: 8px 15px; border-radius: 10px; margin: 5px; display: inline-block;'>🔒 100% Private</span>
                <span style='background: #333; padding: 8px 15px; border-radius: 10px; margin: 5px; display: inline-block;'>🚀 Zero Latency</span>
                <span style='background: #333; padding: 8px 15px; border-radius: 10px; margin: 5px; display: inline-block;'>🌍 Multilingual</span>
            </div>
            <p style='margin-top: 2rem; opacity: 0.6;'>Type your doubt below to start learning.</p>
        </div>
    """, unsafe_allow_html=True)

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# ==================== INFERENCE ====================
prompt = st.chat_input(PLACEHOLDERS.get(st.session_state.language, "Ask anything..."))

if prompt or (st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and len(st.session_state.messages) == 1):
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    else:
        prompt = st.session_state.messages[-1]["content"]

    system_prompt = LANG_SYSTEM_PROMPT.get(st.session_state.language, LANG_SYSTEM_PROMPT["English"])
    messages = [{"role": "system", "content": system_prompt}]
    
    verified_fact = get_current_facts(prompt)
    if verified_fact:
        messages.append({"role": "system", "content": f"IMPORTANT VERIFIED FACT: {verified_fact}"})
    
    for msg in st.session_state.messages: messages.append(msg)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        try:
            with st.spinner("AMD Local Inference in progress..."):
                stream = ollama.chat(
                    model=st.session_state.model,
                    messages=messages,
                    stream=True,
                    options=MODEL_OPTS.get(st.session_state.model, {"temperature": 0.6})
                )
                for chunk in stream:
                    if 'message' in chunk:
                        full_res += chunk['message']['content']
                        placeholder.markdown(full_res + "▌")
                placeholder.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                
                # Auto-save
                chat_entry = {
                    "id": st.session_state.current_chat_id,
                    "language": st.session_state.language,
                    "model": st.session_state.model,
                    "messages": st.session_state.messages,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "preview": st.session_state.messages[0]["content"][:40]
                }
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
