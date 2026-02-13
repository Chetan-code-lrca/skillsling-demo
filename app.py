import streamlit as st
import ollama
import time
import json
import os
from datetime import datetime

# ==================== CONFIG ====================
AVAILABLE_MODELS = ["llama3.2:3b", "gemma2:2b", "phi3:mini"]

PLACEHOLDERS = {
    "Hindi": "Doubt poocho... (Hindi)",
    "English": "Ask your doubt... (English)",
    "Hinglish": "Doubt poocho yaar... (Hinglish)",
    "Tamil": "கேள்வி கேளுங்கள்... (Tamil)",
    "Telugu": "డౌట్‌కు ఏదైనా అడుగు... (Telugu)"
}

LANG_SYSTEM_PROMPT = {
    "Hindi": """You are SkillSling AI – friendly tutor for Class 8-12 students.
जब भी प्रश्न हिंदी में पूछा जाए तो उत्तर 100% हिंदी (देवनागरी लिपि) में दें।
- सरल और स्पष्ट उत्तर दें
- सारणी (table) का उपयोग करें जब आवश्यक हो
- गणित के प्रश्नों में चरण दिखाएं
- प्रोत्साहित करने वाले शब्द प्रयोग करें""",
    
    "English": """You are SkillSling AI – friendly tutor for Class 8-12 students.
Always respond ONLY in English.
- Give simple and clear answers
- Use tables when needed
- Show steps for math problems
- Be encouraging""",
    
    "Hinglish": """You are SkillSling AI – friendly tutor for Class 8-12 students.
Hinglish mein jawaab dein - Hindi + English mix.
- Simple answers dein
- Tables use karin
- Math mein steps dikhayen""",
    
    "Tamil": """You are SkillSling AI – friendly tutor for Class 8-12 students.
தமிழில் மட்டுமே பதில் கூறவும் - Tamil script only.
- எளிதான பதில் கூறவும்
- அட்டவணை பயன்படுத்தவும்
- கணிதத்தில் படிகள் காட்டவும்""",
    
    "Telugu": """You are SkillSling AI – friendly tutor for Class 8-12 students.
Telugu lo em chestunnavo ani reply ivvu - Telugu script only, no English.
- Simple ga ela jawab ivvu
- Tables use chesukovachu
- Maths lo steps peduthu
- E勉勵する (encourage) words use chesuko"""
}

MODEL_OPTS = {
    "llama3.2:3b": {"temperature": 0.7, "num_predict": 1024},
    "gemma2:2b": {"temperature": 0.7, "num_predict": 800},
    "phi3:mini": {"temperature": 0.7, "num_predict": 800}
}

HISTORY_FILE = "chat_history.json"

st.set_page_config(page_title="SkillSling AI", page_icon="🚀", layout="wide")

# CSS
st.markdown("""
    <style>
    .stChatMessage {padding: 1rem; border-radius: 12px; margin: 0.5rem 0;}
    .user {background-color: #e6f3ff;}
    .assistant {background-color: #f0f2f6;}
    </style>
""", unsafe_allow_html=True)

st.title("🚀 SkillSling AI")
st.markdown("🏆 **AMD Slingshot 2026** | 📚 **100% Offline AI Study Tutor**")
st.info("💡 For current affairs/latest news - please check the web. This is an offline study platform.")

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "language" not in st.session_state:
    st.session_state.language = "Hindi"
if "model" not in st.session_state:
    st.session_state.model = "llama3.2:3b"
if "past_chats" not in st.session_state:
    st.session_state.past_chats = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = f"chat_{int(time.time())}"

# ==================== HISTORY FUNCTIONS ====================
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = True
    st.session_state.past_chats = load_history()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("💬 Chat History")
    
    if st.button("✨ New Chat", use_container_width=True):
        if len(st.session_state.messages) > 0:
            chat_entry = {
                "id": st.session_state.current_chat_id,
                "language": st.session_state.language,
                "model": st.session_state.model,
                "messages": st.session_state.messages,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "preview": st.session_state.messages[0]["content"][:40] if st.session_state.messages else "New Chat"
            }
            st.session_state.past_chats.append(chat_entry)
            save_history(st.session_state.past_chats)
        
        st.session_state.current_chat_id = f"chat_{int(time.time())}"
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Previous Chats:**")
    
    if st.session_state.past_chats:
        for idx, chat in enumerate(reversed(st.session_state.past_chats[-10:])):
            real_idx = len(st.session_state.past_chats) - 1 - idx
            chat_lang = chat.get("language", "Hindi")[:3]
            preview = (chat.get("preview") or "Chat")[:25]
            
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"💬 {preview}", key=f"btn_{chat.get('id', real_idx)}"):
                    st.session_state.current_chat_id = chat.get("id", "")
                    st.session_state.messages = chat.get("messages", [])
                    st.session_state.language = chat.get("language", "Hindi")
                    st.session_state.model = chat.get("model", "llama3.2:3b")
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{chat.get('id', real_idx)}"):
                    st.session_state.past_chats.pop(real_idx)
                    save_history(st.session_state.past_chats)
                    st.rerun()
    else:
        st.caption("No past chats")
    
    st.markdown("---")
    st.caption("🏆 AMD Slingshot 2026\n📚 SkillSling Team")

# ==================== TOP SETTINGS ====================
col1, col2 = st.columns([2, 2])

with col1:
    lang_options = ["Hindi", "English", "Hinglish", "Tamil", "Telugu"]
    lang_idx = lang_options.index(st.session_state.language) if st.session_state.language in lang_options else 0
    new_lang = st.selectbox("🌐 Language", lang_options, index=lang_idx)
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.session_state.messages = []

with col2:
    model_idx = AVAILABLE_MODELS.index(st.session_state.model) if st.session_state.model in AVAILABLE_MODELS else 0
    new_model = st.selectbox("🤖 Model", AVAILABLE_MODELS, index=model_idx)
    if new_model != st.session_state.model:
        st.session_state.model = new_model

# ==================== CHAT DISPLAY ====================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==================== INPUT ====================
placeholder = PLACEHOLDERS.get(st.session_state.language, "Ask your doubt...")
prompt = st.chat_input(placeholder)

if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get system prompt for selected language
    system_prompt = LANG_SYSTEM_PROMPT.get(st.session_state.language, LANG_SYSTEM_PROMPT["English"])
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    for msg in st.session_state.messages:
        messages.append(msg)
    
    with st.chat_message("assistant"):
        placeholder_resp = st.empty()
        full_response = ""
        
        with st.spinner("Thinking..."):
            try:
                stream = ollama.chat(
                    model=st.session_state.model,
                    messages=messages,
                    stream=True,
                    options=MODEL_OPTS.get(st.session_state.model, {"temperature": 0.7, "num_predict": 1024})
                )
                
                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        full_response += chunk['message']['content']
                        placeholder_resp.markdown(full_response + "▌")
                        time.sleep(0.02)
                
                placeholder_resp.markdown(full_response)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                full_response = "Error! Please check if Ollama is running."
                placeholder_resp.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

st.markdown("---")
st.caption("💡 Past chats saved in sidebar | 100% Offline Platform")
