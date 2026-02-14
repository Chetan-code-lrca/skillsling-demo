import streamlit as st
import ollama
import time
import json
import os
import io
import google.generativeai as genai
from current_facts import get_current_facts
from datetime import datetime
from pypdf import PdfReader

# ==================== CONFIG ====================
AVAILABLE_MODELS = ["llama3.2:3b", "gemma2:2b", "phi3:mini"]

# Detect mobile/network constraints
import platform
IS_MOBILE_ENV = "arm" in platform.machine().lower() or os.environ.get("STREAMLIT_LOGGER_LEVEL") == "debug"

# Gemini Fallback Setup
GEMINI_API_KEY = None
try:
    # Safely check for secrets without crashing local run
    GEMINI_API_KEY = st.secrets.get("GOOGLE_API_KEY")
except:
    # If no secrets file exists locally, check environment variables
    GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")

if GEMINI_API_KEY:
    # transport='rest' fixes some 404/v1beta issues on cloud hosts
    genai.configure(api_key=GEMINI_API_KEY, transport='rest')

def is_ollama_running():
    try:
        ollama.list()
        return True
    except:
        return False

OLLAMA_ACTIVE = is_ollama_running()
MODE_COLOR = "#00ff00" if OLLAMA_ACTIVE else "#ffcc00"
MODE_TEXT = "⚡ AMD LOCAL MODE" if OLLAMA_ACTIVE else "🌐 CLOUD MODE"

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

# ==================== MOBILE-OPTIMIZED CONFIG ====================
st.set_page_config(
    page_title="SkillSling AI", 
    page_icon="🚀", 
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# ==================== MOBILE-FIRST RESPONSIVE CSS ====================
st.markdown("""
    <style>
    /* Reset and Base */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    /* Main app container */
    .stApp { 
        background-color: #0b0d11 !important; 
        color: #e3e3e3; 
        max-width: 100% !important;
        padding: 0 !important;
    }
    
    /* Main content area */
    .main {
        padding: 12px !important;
    }
    
    /* Hide unnecessary elements */
    #MainMenu, footer, header { visibility: hidden !important; }
    
    /* Chat messages - mobile optimized */
    .stChatMessage {
        border-radius: 8px !important;
        padding: 10px !important;
        margin-bottom: 8px !important;
        max-width: 100% !important;
        width: 100% !important;
        font-size: 15px !important;
        line-height: 1.4 !important;
    }
    
    .stChatMessage p { margin: 0 !important; }
    
    [data-testid="stChatMessageUser"] { 
        background-color: #1a5490 !important; 
        margin-left: 0 !important;
    }
    
    [data-testid="stChatMessageAssistant"] { 
        background-color: #2a2a2a !important;
    }
    
    /* Input container */
    .stChatInputContainer {
        padding: 10px 0 !important;
        position: sticky !important;
        bottom: 0 !important;
        background: #0b0d11 !important;
    }
    
    .stChatInput input {
        font-size: 16px !important;
        padding: 12px !important;
        border-radius: 8px !important;
        min-height: 45px !important;
    }
    
    /* Buttons - touch friendly */
    .stButton button {
        min-height: 44px !important;
        font-size: 14px !important;
        width: 100% !important;
        border-radius: 6px !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #111216 !important;
        width: 85vw !important;
    }
    
    .stSelectbox, .stFileUploader {
        font-size: 14px !important;
    }
    
    /* Headers */
    h1, h2, h3 { 
        margin-bottom: 12px !important;
        line-height: 1.2 !important;
    }
    
    h1 { font-size: 24px !important; }
    h2 { font-size: 18px !important; }
    h3 { font-size: 16px !important; }
    
    /* Text sizes */
    p, span, div { font-size: 14px !important; }
    
    .metric-text { 
        font-size: 12px !important; 
        opacity: 0.6 !important; 
        margin: 8px 0 !important;
    }
    
    .perf-badge {
        background: linear-gradient(90deg, #ed1c24 0%, #000000 100%) !important;
        padding: 6px 10px !important;
        border-radius: 16px !important;
        font-size: 11px !important;
        font-weight: bold !important;
        color: white !important;
        border: 1px solid #ed1c24 !important;
        display: inline-block !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0b0d11; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
    
    /* Expanders */
    .streamlit-expanderHeader { padding: 10px !important; }
    
    /* Messages container */
    [data-testid="stChatMessageContainer"] {
        gap: 0 !important;
    }
    
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
    st.markdown(f"<h2 style='color: #ed1c24 !important; text-align: center;'>SKILLSLING</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='perf-badge' style='border-color: {MODE_COLOR}; color: {MODE_COLOR};'>{MODE_TEXT}</div>", unsafe_allow_html=True)
    
    if not OLLAMA_ACTIVE:
        st.warning("Ollama not detected. Falling back to Cloud AI.")
        with st.expander("ℹ️ API Status"):
            if GEMINI_API_KEY:
                st.success("✅ Gemini API Key found")
            else:
                st.error("❌ Gemini API Key missing")
        with st.expander("How to use AMD Local on Mobile?"):
            st.write("1. Open terminal on laptop.")
            st.write("2. Note the 'Network URL' (e.g. 192.168.x.x).")
            st.write("3. Open that URL on your phone's browser.")
    
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
        st.success("✅ Notes Attached!")

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
col1, col2 = st.columns([0.9, 0.1])
with col2:
    if st.button("🎤", help="Voice Input (Mobile Friendly)"):
        st.toast("Voice input feature coming soon or use your mobile keyboard's mic!")

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
            if OLLAMA_ACTIVE:
                stream = ollama.chat(model=st.session_state.model, messages=messages, stream=True, options=MODEL_OPTS)
                for chunk in stream:
                    if 'message' in chunk:
                        full_res += chunk['message']['content']
                        p_hold.markdown(full_res + "▌")
            else:
                # Gemini Fallback Logic - simplified for mobile reliability
                if not GEMINI_API_KEY:
                    st.error("🔑 **Google API Key Missing:** Add `GOOGLE_API_KEY` to Streamlit Secrets.")
                    st.stop()
                
                # Use Gemini's chat interface for better stability
                test_models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]
                success = False
                last_err = ""

                for m_name in test_models:
                    try:
                        model = genai.GenerativeModel(
                            m_name,
                            system_instruction=sys_p
                        )
                        
                        # Build conversation history for Gemini
                        chat_history = []
                        for msg in st.session_state.messages[:-1]:  # All but current user message
                            if msg["role"] in ["user", "assistant"]:
                                chat_history.append({
                                    "role": msg["role"],
                                    "parts": [msg["content"]]
                                })
                        
                        chat = model.start_chat(history=chat_history)
                        
                        # Build user input with context
                        user_input = st.session_state.messages[-1]["content"]
                        
                        # Add context if available
                        if st.session_state.context_text:
                            user_input += f"\n\n[Context from notes:\n{st.session_state.context_text[:1500]}]"
                        
                        # Add facts if available
                        fact = get_current_facts(user_input)
                        if fact:
                            user_input += f"\n\n[Relevant fact: {fact}]"
                        
                        response = chat.send_message(user_input)
                        
                        full_res = response.text
                        p_hold.markdown(full_res)
                        success = True
                        break
                    except Exception as e:
                        last_err = str(e)
                        continue
                
                if not success:
                    if "API_KEY" in last_err or "GOOGLE_API_KEY" in last_err or "not authenticated" in last_err:
                        st.error("🔑 **API Key Issue:** Make sure GOOGLE_API_KEY is set in Streamlit Secrets")
                    elif "400" in last_err or "streaming" in last_err.lower():
                        st.error("⚠️ **Network Issue:** Please reload and try again. If persistent, try different language/model.")
                    else:
                        st.error(f"❌ Cloud AI Error: {last_err[:200]}")
                    st.stop()

            duration = round(time.time() - start_t, 2)
            p_hold.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res, "perf": duration})
            
            chat_entry = {"id": st.session_state.current_chat_id, "messages": st.session_state.messages, "preview": st.session_state.messages[0]["content"][:40]}
            if not any(c.get("id") == chat_entry["id"] for c in st.session_state.past_chats):
                st.session_state.past_chats.append(chat_entry)
            save_history(st.session_state.past_chats)
        except Exception as e:
            st.error(f"Inference Error: {str(e)}")

# ==================== MOBILE KEYBOARD FIX ====================
# ✅ Ensures input field scrolls into view when keyboard opens
st.markdown("""
    <script>
    const input = window.parent.document.querySelector('input[data-testid="stChatInput"]');
    if (input) {
        input.addEventListener('focus', () => {
            setTimeout(() => {
                input.scrollIntoView({behavior: 'smooth', block: 'end'});
            }, 300);
        });
    }
    </script>
""", unsafe_allow_html=True)
