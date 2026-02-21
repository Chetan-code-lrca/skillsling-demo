import streamlit as st
import ollama
import time
import tempfile
import os
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

# ==================== CONFIG ====================
AVAILABLE_MODELS = [
    "llama3.2:3b",
    "llama3.1:8b",
    "qwen2.5:7b-instruct",
    "phi3:mini"
]

SUBJECT_MODEL_RECOMMENDATIONS = {
    "General": "llama3.1:8b",
    "English": "llama3.1:8b",
    "Social Science": "llama3.1:8b",
    "Mathematics": "qwen2.5:7b-instruct",
    "Science": "qwen2.5:7b-instruct",
}

PLACEHOLDERS = {
    "Hindi": "अपना सवाल यहाँ लिखें...",
    "English": "Type your question here...",
    "Hinglish": "Apna sawaal yahan likhein...",
    "Tamil": "உங்கள் கேள்வியை இங்கே எழுதுங்கள்...",
    "Telugu": "మీ ప్రశ్నను ఇక్కడ టైప్ చేయండి..."
}

LANGUAGE_SYSTEM_PROMPTS = {
    "Hindi": """You are a Hindi tutor. Answer ONLY in Hindi (Devanagari script). No English letters at all. Use simple language. Follow NCERT style.""",
    "English": """You are a helpful tutor for Indian students. Answer ONLY in English. Use clear, simple words. Be accurate and encouraging. Follow NCERT guidelines.""",
    "Hinglish": """You are a Hinglish tutor (Roman script only). Mix Hindi + English naturally. Keep it simple and friendly.""",
    "Tamil": """நீங்கள் தமிழ் ஆசிரியர். தமிழில் மட்டுமே பதிலளிக்கவும். எளிய மொழியைப் பயன்படுத்தவும்.""",
    "Telugu": """మీరు తెలుగు ఉపాధ్యాయులు. తెలుగులో మాత్రమే సమాధానం ఇవ్వండి. సులభమైన భాష వాడండి."""
}

# Subject-specific depth instructions (this is the game-changer)
DEPTH_INSTRUCTIONS = {
    "Science": """
For science questions always include:
• Exact cellular / organelle location (e.g. thylakoid membrane, stroma, matrix)
• Key enzymes with full names (e.g. RuBisCO, ATP synthase)
• Balanced chemical equations when relevant
• ATP / NADPH / electron / proton counts when applicable
• Important related concepts (photorespiration in C3, C4 vs CAM differences, etc.)
• Use precise scientific terminology but explain simply for school students
""",
    "Mathematics": """
For mathematics questions:
• Always show every algebraic / logical step clearly
• Use proper mathematical notation
• Explain why each step is valid (property, theorem, rule)
• For calculus: clearly state antiderivative, apply limits, mention Fundamental Theorem
• For definite integrals: show F(b) - F(a) calculation
""",
    "English": """
For English grammar/vocabulary questions:
• Clearly state the grammar rule being applied
• Show the corrected sentence
• Give 1–2 similar correct examples
• If vocabulary, provide meaning + one natural sentence using it
""",
    # Add more subjects later if needed
}

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="SkillSling • AMD Slingshot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark + mobile style
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0b0d11, #1a1d23); color: #e3e3e3; }
    section[data-testid="stSidebar"] { background: #111216 !important; border-right: 2px solid #ed1c24; }
    .stChatMessage { border-radius: 12px; padding: 1.1rem; margin: 0.5rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.4); }
    [data-testid="stChatMessageUser"]   { background: linear-gradient(135deg, #1e2028, #2a2d35) !important; border-left: 4px solid #ed1c24; }
    [data-testid="stChatMessageAssistant"] { background: linear-gradient(135deg, #1a1d24, #23252e) !important; border-left: 4px solid #00ff88; }
    .amd-badge { background: linear-gradient(90deg, #ed1c24, #ff4444); padding: 6px 14px; border-radius: 20px; color:white; font-weight:bold; font-size:0.78rem; border:1px solid #ff0000; box-shadow:0 0 15px rgba(237,28,36,0.4); display:inline-block; }
    .model-info  { font-size:0.78rem; opacity:0.7; margin:8px 0 4px; padding:3px 9px; background:rgba(0,255,136,0.06); border-radius:6px; text-align:right; }
    #MainMenu, footer {visibility: hidden;}
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] { width:0 !important; visibility:hidden !important; }
        section[data-testid="stSidebar"][aria-expanded="true"] { width:80vw !important; visibility:visible !important; z-index:999; position:fixed; top:0; left:0; height:100vh; box-shadow:3px 0 20px rgba(0,0,0,0.7); }
        .stChatInput { position:fixed; bottom:0; left:0; right:0; background:#0b0d11; z-index:998; padding:10px; box-shadow:0 -5px 15px rgba(0,0,0,0.6); }
        .main .block-container { padding-bottom:110px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
defaults = {
    "messages": [],
    "subject": "General",
    "language": "English",
    "model": "llama3.1:8b",
    "vector_store": None,
    "total_inference_time": 0.0,
    "query_count": 0,
    "language_change_counter": 0
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("<div style='text-align:center; margin:20px 0;'><h2 style='color:#ed1c24; margin-bottom:8px;'>SKILLSLING</h2><div class='amd-badge'>AMD SLINGSHOT 2026</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='amd-badge' style='margin:12px 0;'>Offline • AMD Powered</div>", unsafe_allow_html=True)

    try:
        ollama.list()
        st.success("Ollama Running", icon="✅")
    except:
        st.error("Ollama not running", icon="❌")
        st.caption("Run in terminal:  `ollama serve`")

    st.markdown("---")

    st.subheader("Language")
    new_lang = st.selectbox("", list(PLACEHOLDERS.keys()), index=list(PLACEHOLDERS.keys()).index(st.session_state.language), label_visibility="collapsed")
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.session_state.language_change_counter += 1
        st.rerun()

    st.subheader("Subject")
    prev_subject = st.session_state.subject
    st.session_state.subject = st.selectbox("", list(SUBJECT_MODEL_RECOMMENDATIONS.keys()), label_visibility="collapsed")

    if st.session_state.subject != prev_subject:
        rec = SUBJECT_MODEL_RECOMMENDATIONS.get(st.session_state.subject, "llama3.1:8b")
        if st.session_state.model != rec and rec in AVAILABLE_MODELS:
            st.session_state.model = rec
            st.toast(f"Switched to optimized model for {st.session_state.subject}", icon="🔧")

    st.subheader("AI Model")
    st.session_state.model = st.selectbox("", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model) if st.session_state.model in AVAILABLE_MODELS else 0, label_visibility="collapsed")

    st.caption(f"🧠 Active: **{st.session_state.model}**  •  Optimized for **{st.session_state.subject}**")

    # PDF upload
    st.subheader("Study Material")
    pdf = st.file_uploader("Upload PDF notes", type="pdf")
    if pdf:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
            tf.write(pdf.read())
            path = tf.name
        with st.spinner("Indexing PDF..."):
            loader = PyPDFLoader(path)
            docs = loader.load()
            chunks = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=120).split_documents(docs)
            st.session_state.vector_store = FAISS.from_documents(chunks, OllamaEmbeddings(model=st.session_state.model))
            st.success(f"PDF indexed ({len(docs)} pages)")
        os.unlink(path)

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        for k in ["messages", "total_inference_time", "query_count"]:
            st.session_state[k] = defaults[k]
        st.rerun()

# ==================== MAIN AREA ====================
st.caption(f"🧠 Active model: **{st.session_state.model}**  •  Optimized for **{st.session_state.subject}**")

if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; padding:80px 20px;">
        <h1 style="color:#ed1c24; font-size:3.4rem; margin-bottom:0.3rem;">SkillSling AI</h1>
        <p style="font-size:1.25rem; opacity:0.9; margin:0.6rem 0 1.4rem;">Your powerful offline tutor – tuned for high accuracy & depth</p>
        <div class="amd-badge" style="font-size:1.05rem; padding:10px 18px;">AMD SLINGSHOT 2026</div>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "latency" in msg:
            st.markdown(f'<div class="model-info">⚡ {msg["latency"]:.1f}s</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────
if prompt := st.chat_input(PLACEHOLDERS.get(st.session_state.language, "Ask anything...")):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        # Build enhanced system prompt
        base = LANGUAGE_SYSTEM_PROMPTS.get(st.session_state.language, LANGUAGE_SYSTEM_PROMPTS["English"])

        if st.session_state.subject in DEPTH_INSTRUCTIONS:
            base += DEPTH_INSTRUCTIONS[st.session_state.subject]

        system = base + f"\nCurrent subject focus: {st.session_state.subject}"

        msgs = [{"role": "system", "content": system}]

        if len(st.session_state.messages) <= 2:
            msgs.append({"role": "user", "content": f"From now on answer ONLY in {st.session_state.language} language."})

        for m in st.session_state.messages:
            msgs.append({"role": m["role"], "content": m["content"]})

        start = time.time()

        try:
            stream = ollama.chat(
                model=st.session_state.model,
                messages=msgs,
                stream=True,
                options={
                    "temperature": 0.0,
                    "top_k": 30,
                    "top_p": 0.65,
                    "repeat_penalty": 1.25
                }
            )

            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    full_response += chunk['message']['content']
                    placeholder.markdown(full_response + "▌")

            # Invisible correction step
            check = f"""Strict academic checker.
Read the answer below.
If ANY factual error, math mistake, incomplete step, wrong unit, or language issue → output the FULL corrected version.
If correct and complete → output the text EXACTLY as is (copy-paste).
NEVER explain. NEVER say "corrected" or "this is right". Output ONLY the clean final answer.

Answer:
{full_response}"""

            verification = ollama.chat(
                model=st.session_state.model,
                messages=[{"role": "user", "content": check}],
                options={"temperature": 0.0, "top_p": 0.6}
            )

            final = verification['message']['content'].strip() or full_response

            latency = time.time() - start
            placeholder.markdown(final)
            st.markdown(f'<div class="model-info">⚡ {latency:.1f}s • {st.session_state.model}</div>', unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": final,
                "latency": latency
            })
            st.session_state.total_inference_time += latency
            st.session_state.query_count += 1

        except Exception as e:
            placeholder.markdown(f"Error: {str(e)}\n\nIs Ollama running?")