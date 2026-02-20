import streamlit as st
import ollama
import time
import tempfile
import os
import json
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

# ==================== CONFIG ====================
AVAILABLE_MODELS = ["llama3.2:3b", "gemma2:2b", "phi3:mini"]

PLACEHOLDERS = {
    "Hindi": "अपना सवाल यहाँ लिखें...",
    "English": "Type your question here...",
    "Hinglish": "Apna sawaal yahan likhein...",
    "Tamil": "உங்கள் கேள்வியை இங்கே எழுதுங்கள்...",
    "Telugu": "మీ ప్రశ్నను ఇక్కడ టైప్ చేయండి..."
}

# ULTRA-STRONG LANGUAGE ENFORCEMENT
LANGUAGE_SYSTEM_PROMPTS = {
    "Hindi": """तुम एक हिंदी शिक्षक हो।
अनिवार्य नियम (3 बार दोहराओ):
1. केवल हिंदी देवनागरी लिपि में उत्तर दो। केवल हिंदी में। केवल हिंदी में।
2. कोई भी अंग्रेजी अक्षर, शब्द, वाक्य मत लिखो – एक भी नहीं।
3. तकनीकी शब्दों को भी हिंदी में समझाओ।
4. सरल हिंदी बोलो।
5. छात्र को प्रोत्साहित करो।
गलत उदाहरण: "Photosynthesis is..."
सही उदाहरण: "प्रकाश संश्लेषण एक प्रक्रिया है..."
NCERT दिशा-निर्देशों का पालन करो।""",
    
    "English": """You are an English tutor for Indian students.
MANDATORY RULES (repeat 3 times):
1. Respond ONLY in English language. ONLY in English. ONLY in English.
2. Use simple, clear English words.
3. Explain concepts in an easy-to-understand manner.
4. Encourage the student positively.
5. Follow NCERT curriculum guidelines.
Wrong example: "फोटोसिंथेसिस क्या है?"
Correct example: "Photosynthesis is the process by which plants make their own food using sunlight..."
Answer only what is asked.""",
    
    "Hinglish": """Tum ek Hinglish tutor ho (Roman script mein Hindi + English mix).
MANDATORY RULES (repeat 3 times):
1. Hindi aur English mix karke likhna hai. ONLY Roman script.
2. Devanagari mat use karo.
3. Simple words use karo.
4. Student ko encourage karo.
Sirf jo pucha hai wahi jawab do.
Example: "Photosynthesis kya hai?" → "Photosynthesis ek process hai jisme plants sunlight se khana banate hain..." """,
    
    "Tamil": """நீங்கள் ஒரு தமிழ் ஆசிரியர்.
கட்டாய விதிகள் (3 முறை சொல்லுங்கள்):
1. தமிழ் எழுத்துகளில் மட்டுமே பதிலளிக்க வேண்டும். மட்டும் தமிழில். மட்டும் தமிழில்.
2. ஆங்கில எழுத்துகள் பயன்படுத்த வேண்டாம்.
3. எளிய தமிழ் சொற்களைப் பயன்படுத்தவும்.
4. மாணவரை ஊக்குவிக்கவும்.
தவறான உதாரணம்: "Photosynthesis is..."
சரியான உதாரணம்: "ஒளிச்சேர்க்கை என்பது..." """,
    
    "Telugu": """మీరు తెలుగు ఉపాధ్యాయులు.
తప్పనిసరి నియమాలు (3 సార్లు పునరావృతం చేయండి):
1. తెలుగు లిపిలో మాత్రమే సమాధానం ఇవ్వాలి. మాత్రమే తెలుగులో. మాత్రమే తెలుగులో.
2. ఆంగ్ల అక్షరాలు వాడకూడదు.
3. సులభమైన తెలుగు పదాలను ఉపయోగించండి.
4. విద్యార్థిని ప్రోత్సహించండి.
తప్పు ఉదాహరణ: "Photosynthesis is..."
సరైన ఉదాహరణ: "కాంతి సంశ్లేషణ అనేది..." """
}

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="SkillSling - AMD Slingshot 2026",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"   # Mobile-first: sidebar collapsed by default
)

# ==================== PWA + PROFESSIONAL DARK UI + MOBILE RESPONSIVE ====================
st.markdown("""
    <style>
    /* Your beautiful dark AMD theme */
    .stApp {
        background: linear-gradient(135deg, #0b0d11 0%, #1a1d23 100%);
        color: #e3e3e3;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #111216 !important;
        border-right: 2px solid #ed1c24;
    }
    
    .stChatMessage {
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    
    [data-testid="stChatMessageUser"] {
        background: linear-gradient(135deg, #1e2028 0%, #2a2d35 100%) !important;
        border-left: 4px solid #ed1c24;
    }
    
    [data-testid="stChatMessageAssistant"] {
        background: linear-gradient(135deg, #1a1d24 0%, #23252e 100%) !important;
        border-left: 4px solid #00ff88;
    }
    
    .amd-badge {
        background: linear-gradient(90deg, #ed1c24 0%, #ff4444 100%);
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        color: white;
        text-transform: uppercase;
        border: 2px solid #ff0000;
        display: inline-block;
        margin: 5px 0;
        box-shadow: 0 0 20px rgba(237, 28, 36, 0.5);
    }
    
    .perf-metric {
        font-size: 0.7rem;
        opacity: 0.6;
        font-family: 'Courier New', monospace;
        margin-top: 8px;
        padding: 4px 8px;
        background: rgba(0, 255, 136, 0.1);
        border-radius: 4px;
        display: inline-block;
    }
    
    #MainMenu, footer {visibility: hidden;}
    
    /* MOBILE RESPONSIVE – fixes sidebar and input */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            min-width: 0 !important;
            width: 0 !important;
            visibility: hidden !important;
            overflow: hidden !important;
            transition: all 0.3s ease;
        }
        
        section[data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 85vw !important;
            width: 85vw !important;
            visibility: visible !important;
            z-index: 1000 !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            overflow-y: auto !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.6);
        }
        
        .stChatInput {
            padding-bottom: 100px !important;
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            background: #0b0d11 !important;
            z-index: 999 !important;
            box-shadow: 0 -4px 12px rgba(0,0,0,0.5);
        }
        
        .main .block-container {
            padding-bottom: 140px !important;
        }
        
        .stChatMessage {
            font-size: 16px !important;
            padding: 0.8rem !important;
        }
        
        h1 { font-size: 1.8rem !important; }
        h2, h3 { font-size: 1.4rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# ==================== PWA (Installable on Phone) ====================
st.markdown("""
    <link rel="manifest" href="data:application/manifest+json;base64,eyJuYW1lIjoiU2tpbGxTbGluZyIsInNob3J0X25hbWUiOiJTa2lsbFNsaW5nIiwic3RhcnRfdXJsIjoiLiIsImRpc3BsYXkiOiJzdGFuZGFsb25lIiwiYmFja2dyb3VuZF9jb2xvciI6IiMwYjBkMTEiLCJ0aGVtZV9jb2xvciI6IiNlZDFjMjQifQ==" />
    <meta name="theme-color" content="#ed1c24">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "subject" not in st.session_state:
    st.session_state.subject = "General"
if "language" not in st.session_state:
    st.session_state.language = "English"
if "model" not in st.session_state:
    st.session_state.model = AVAILABLE_MODELS[0]
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "total_inference_time" not in st.session_state:
    st.session_state.total_inference_time = 0
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
if "last_language" not in st.session_state:
    st.session_state.last_language = "English"
if "language_change_counter" not in st.session_state:
    st.session_state.language_change_counter = 0

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h1 style='color: #ed1c24; margin-bottom: 5px;'>SKILLSLING</h1>
            <div class='amd-badge'>⚡ AMD SLINGSHOT 2026</div>
            <p style='font-size: 0.75rem; opacity: 0.7; margin-top: 10px;'>
                Offline AI Tutor | 100% Local Inference
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Light hybrid badge
    st.markdown("""
        <div class='amd-badge' style='margin: 10px 0;'>
            Offline Mode – AMD Powered
        </div>
    """, unsafe_allow_html=True)

    # Ollama status
    try:
        ollama.list()
        st.success("✅ Ollama Running")
    except:
        st.error("❌ Ollama Not Running!")
        st.caption("Start Ollama: `ollama serve`")
    st.markdown("---")

    # Language selection
    st.subheader("🌐 Language")
    new_language = st.selectbox(
        "Choose your preferred language",
        ["English", "Hindi", "Hinglish", "Tamil", "Telugu"],
        index=["English", "Hindi", "Hinglish", "Tamil", "Telugu"].index(st.session_state.language)
    )
    
    if new_language != st.session_state.language:
        st.session_state.language = new_language
        st.session_state.last_language = new_language
        st.session_state.language_change_counter += 1
        st.rerun()

    # Subject & Model
    st.subheader("📚 Subject")
    st.session_state.subject = st.selectbox("Select your subject", ["General", "Mathematics", "Science", "English", "Social Science"], index=0)

    st.subheader("🤖 AI Model")
    st.session_state.model = st.selectbox("Select AI model", AVAILABLE_MODELS, index=0)

    # PDF upload
    st.subheader("📄 Study Material")
    use_pdf = st.checkbox("Use uploaded PDF context", value=False)
    uploaded_file = st.file_uploader("Upload your notes (PDF)", type="pdf")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        with st.spinner("🔄 Processing PDF..."):
            try:
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                splits = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100).split_documents(docs)
                st.session_state.vector_store = FAISS.from_documents(splits, OllamaEmbeddings(model=st.session_state.model))
                st.success(f"✅ PDF processed ({len(docs)} pages)")
            except Exception as e:
                st.error(f"❌ PDF processing failed: {str(e)}")
        os.unlink(tmp_path)

    st.markdown("---")

    # Performance
    if st.session_state.query_count > 0:
        avg_time = st.session_state.total_inference_time / st.session_state.query_count
        st.subheader("📊 Performance")
        st.metric("Queries Processed", st.session_state.query_count)
        st.metric("Avg Response Time", f"{avg_time:.2f}s")
        st.metric("Total Inference", f"{st.session_state.total_inference_time:.1f}s")

    st.markdown("---")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_inference_time = 0
        st.session_state.query_count = 0
        st.rerun()

    if st.button("💾 Export Chat (JSON)", use_container_width=True):
        if st.session_state.messages:
            chat_data = {
                "export_time": datetime.now().isoformat(),
                "language": st.session_state.language,
                "model": st.session_state.model,
                "subject": st.session_state.subject,
                "messages": st.session_state.messages
            }
            st.download_button(
                "Download JSON",
                json.dumps(chat_data, ensure_ascii=False, indent=2),
                file_name=f"skillsling_chat_{int(time.time())}.json",
                mime="application/json"
            )

    st.markdown("---")
    st.caption("Built by SkillSling Team")
    st.caption("Powered by AMD GPUs")

# ==================== MAIN CONTENT ====================
if not st.session_state.messages:
    st.markdown("""
        <div style='text-align:center; padding: 60px 20px;'>
            <h1 style='color:#ed1c24; font-size: 3rem; margin-bottom: 10px;'>🚀 SkillSling AI</h1>
            <p style='font-size: 1.2rem; opacity: 0.8; margin-bottom: 30px;'>Your Offline Intelligent Tutor</p>
            <div class='amd-badge' style='font-size: 0.9rem;'>⚡ POWERED BY AMD SLINGSHOT</div>
            <p style='margin-top: 30px; font-size: 0.95rem; opacity: 0.7;'>
                • Multi-language support (5 languages)<br>
                • 100% offline & private<br>
                • PDF note integration<br>
                • NCERT-aligned responses
            </p>
        </div>
    """, unsafe_allow_html=True)

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "latency" in msg:
            st.markdown(f"<div class='perf-metric'>⚡ {msg['latency']:.2f}s | AMD Optimized</div>", unsafe_allow_html=True)

# Dynamic placeholder + force re-mount
current_placeholder = PLACEHOLDERS.get(st.session_state.language, "Type your question...")
prompt = st.chat_input(
    current_placeholder,
    key=f"chat_input_{st.session_state.language}_{st.session_state.get('language_change_counter', 0)}"
)

# ==================== CHAT LOGIC ====================
if prompt:
    print(f"DEBUG: INPUT CAPTURED! Prompt: '{prompt}' | Language: {st.session_state.language} | Model: {st.session_state.model}")

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        ollama_messages = []
        language_prompt = LANGUAGE_SYSTEM_PROMPTS.get(st.session_state.language, LANGUAGE_SYSTEM_PROMPTS["English"])
        ollama_messages.append({"role": "system", "content": f"{language_prompt}\n\nSubject Focus: {st.session_state.subject}"})

        if len(st.session_state.messages) == 2:  # First user message
            ollama_messages.append({"role": "user", "content": f"Important: From now on reply ONLY in {st.session_state.language}. No English at all. Start now."})

        for msg in st.session_state.messages:
            ollama_messages.append(msg)

        start_time = time.time()
        with st.spinner(f"🤔 Thinking in {st.session_state.language}..."):
            try:
                stream = ollama.chat(model=st.session_state.model, messages=ollama_messages, stream=True)
                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        full_response += chunk['message']['content']
                        placeholder.markdown(full_response + "▌")
                        time.sleep(0.01)
                placeholder.markdown(full_response)
                latency = time.time() - start_time

                st.session_state.total_inference_time += latency
                st.session_state.query_count += 1

                st.markdown(f"<div class='perf-metric'>⚡ {latency:.2f}s | AMD Optimized</div>", unsafe_allow_html=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "latency": latency,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                st.error(f"Error: {str(e)}")
                placeholder.markdown("Sorry bhai, kuch gadbad ho gayi. Ollama chal raha hai?")

st.caption("Pro Tip: Change language anytime – your chat history stays preserved!")