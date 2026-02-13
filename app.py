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
    "Telugu": "డाउट पूछो... (Telugu)"
}

LANG_FORCE_PROMPT = {
    "Hindi": "उत्तर 100% हिंदी में दें।\n\n",
    "English": "Answer in English only.\n\n",
    "Hinglish": "Hinglish mein jawaab dein.\n\n",
    "Tamil": "தமிழில் பதில் கூறவும்.\n\n",
    "Telugu": "Telugu lo javab ivvu.\n\n"
}

MODEL_OPTS = {
    "llama3.2:3b": {"temperature": 0.5, "num_predict": 200},
    "gemma2:2b": {"temperature": 0.5, "num_predict": 150},
    "phi3:mini": {"temperature": 0.5, "num_predict": 150}
}

SYSTEM_PROMPT = """You are SkillSling AI – friendly tutor for Class 8-12 students.
- Give helpful, detailed answers
- Use tables for formulas/values
- For math: show step-by-step
- Never say you are AI - act as a friendly tutor
- If asked about current affairs, CMs, news, politics: Explain this is an OFFLINE study platform and suggest checking the web for latest information"""

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
st.info("💡 **Tip:** This is an OFFLINE platform for study. For current affairs, news, or latest information, please check the web.")

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
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
                data = json.load(f)
                for chat in data:
                    if chat.get("id") is None:
                        chat["id"] = f"chat_{time.time()}_{id(chat)}"
                return data
        except: return []
    return []

def save_history(history):
    for chat in history:
        if chat.get("id") is None:
            chat["id"] = f"chat_{time.time()}"
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = True
    st.session_state.past_chats = load_history()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("💬 Chat History")
    
    if st.button("✨ New Chat", use_container_width=True):
        if len(st.session_state.messages) > 1:
            chat_entry = {
                "id": st.session_state.current_chat_id,
                "language": st.session_state.language,
                "model": st.session_state.model,
                "messages": st.session_state.messages[1:],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "preview": st.session_state.messages[1]["content"][:40] if len(st.session_state.messages) > 1 else "Chat"
            }
            existing_idx = next((i for i, c in enumerate(st.session_state.past_chats) if c.get("id") == st.session_state.current_chat_id), None)
            if existing_idx is not None:
                st.session_state.past_chats[existing_idx] = chat_entry
            else:
                st.session_state.past_chats.append(chat_entry)
            save_history(st.session_state.past_chats)
        
        st.session_state.current_chat_id = f"chat_{int(time.time())}"
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Previous Chats:**")
    
    if st.session_state.past_chats:
        for idx, chat in enumerate(reversed(st.session_state.past_chats[-15:])):
            real_idx = len(st.session_state.past_chats) - 1 - idx
            chat_id = chat.get("id") or f"chat_{real_idx}"
            chat_lang = (chat.get("language") or "Hindi")[:3]
            preview = (chat.get("preview") or "Chat")[:20]
            
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"💬 {preview}... ({chat_lang})", key=f"btn_{chat_id}_{real_idx}"):
                    if len(st.session_state.messages) > 1:
                        current_entry = {
                            "id": st.session_state.current_chat_id,
                            "language": st.session_state.language,
                            "model": st.session_state.model,
                            "messages": st.session_state.messages[1:],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "preview": st.session_state.messages[1]["content"][:40]
                        }
                        existing = next((i for i, c in enumerate(st.session_state.past_chats) if c.get("id") == st.session_state.current_chat_id), None)
                        if existing is not None:
                            st.session_state.past_chats[existing] = current_entry
                        else:
                            st.session_state.past_chats.append(current_entry)
                        save_history(st.session_state.past_chats)
                    
                    st.session_state.current_chat_id = chat_id
                    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat.get("messages", [])
                    st.session_state.language = chat.get("language", "Hindi")
                    st.session_state.model = chat.get("model", "llama3.2:3b")
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{chat_id}_{real_idx}"):
                    st.session_state.past_chats.pop(real_idx)
                    save_history(st.session_state.past_chats)
                    st.rerun()
    else:
        st.caption("No past chats yet")
    
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
        st.session_state.messages[0]["content"] = SYSTEM_PROMPT

with col2:
    model_idx = AVAILABLE_MODELS.index(st.session_state.model) if st.session_state.model in AVAILABLE_MODELS else 0
    new_model = st.selectbox("🤖 Model", AVAILABLE_MODELS, index=model_idx)
    if new_model != st.session_state.model:
        st.session_state.model = new_model
        st.session_state.messages[0]["content"] = SYSTEM_PROMPT

# ==================== CHAT DISPLAY ====================
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==================== INPUT ====================
placeholder = PLACEHOLDERS.get(st.session_state.language, "Ask your doubt...")
prompt = st.chat_input(placeholder)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        placeholder_resp = st.empty()
        full_response = ""
        
        with st.spinner("Thinking..."):
            try:
                user_msg = LANG_FORCE_PROMPT.get(st.session_state.language, "") + prompt
                stream = ollama.chat(
                    model=st.session_state.model,
                    messages=st.session_state.messages,
                    stream=True,
                    options=MODEL_OPTS.get(st.session_state.model, {"temperature": 0.5, "num_predict": 200})
                )
                
                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        full_response += chunk['message']['content']
                        placeholder_resp.markdown(full_response + "▌")
                        time.sleep(0.015)
                placeholder_resp.markdown(full_response)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                full_response = "Error! Is Ollama running?"
                placeholder_resp.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # Save
        chat_entry = {
            "id": st.session_state.current_chat_id,
            "language": st.session_state.language,
            "model": st.session_state.model,
            "messages": st.session_state.messages[1:],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "preview": prompt[:40]
        }
        existing_idx = next((i for i, c in enumerate(st.session_state.past_chats) if c.get("id") == st.session_state.current_chat_id), None)
        if existing_idx is not None:
            st.session_state.past_chats[existing_idx] = chat_entry
        else:
            st.session_state.past_chats.append(chat_entry)
        save_history(st.session_state.past_chats)

st.markdown("---")
st.caption("💡 100% Offline Platform | Past chats auto-saved in sidebar | For latest info, check the web")
