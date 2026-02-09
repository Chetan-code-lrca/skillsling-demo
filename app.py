import streamlit as st
import ollama
import time
import tempfile
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

# ==================== CONFIG ====================
MODEL = "llama3.2:3b"  # Fast, good Hindi/English, low RAM

BASE_SYSTEM_PROMPT = """
You are SkillSling AI – friendly bhaiya/didi tutor for Class 8-12 students.
Explain in simple {language} or {language}-English mix.
Be encouraging: "शाबाश!", "Great job!", "Tu topper banega!"
Keep answers short: 4-6 lines max + table if needed.
Current subject: {subject}.
Use PDF context if provided and relevant.
"""

st.set_page_config(page_title="SkillSling AI", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stChatMessage {padding: 1rem; border-radius: 12px; margin: 0.5rem 0;}
    .user {background-color: #e6f3ff;}
    .assistant {background-color: #f0f2f6;}
    </style>
""", unsafe_allow_html=True)

st.title("🚀 SkillSling AI")
st.caption(f"Offline Tutor | Model: {MODEL} | 100% Local")

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "subject" not in st.session_state:
    st.session_state.subject = "General"
if "language" not in st.session_state:
    st.session_state.language = "Hindi"
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# Sidebar
with st.sidebar:
    st.header("Controls")
    st.info("Ollama must be running!")

    language = st.selectbox("Language", ["Hindi", "English", "Hinglish", "Tamil", "Telugu"], index=0)
    if language != st.session_state.language:
        st.session_state.language = language
        st.session_state.messages = []
        st.rerun()

    subject = st.selectbox("Subject", ["General", "Maths", "Science", "English"], index=0)
    if subject != st.session_state.subject:
        st.session_state.subject = subject
        st.rerun()

    use_pdf = st.checkbox("Use uploaded PDF for answers", value=True)

    uploaded_file = st.file_uploader("Upload PDF Notes", type=["pdf"])
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=150)
            splits = text_splitter.split_documents(docs)
            embeddings = OllamaEmbeddings(model=MODEL)
            st.session_state.vector_store = FAISS.from_documents(splits, embeddings)
            st.success("PDF processed successfully! Now ask questions.")
        except Exception as e:
            st.error(f"PDF processing failed: {str(e)}")
        finally:
            os.unlink(tmp_path)

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.caption("Made by Chetan Inaganti – #1 in Slingshot 2026 Loading... ⭐")

# System prompt
system_content = BASE_SYSTEM_PROMPT.format(language=st.session_state.language, subject=st.session_state.subject)
if not st.session_state.messages or st.session_state.messages[0]["role"] != "system":
    st.session_state.messages.insert(0, {"role": "system", "content": system_content})

# Display chat history
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input area
prompt = st.chat_input(f"Doubt poocho... ({st.session_state.language})")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        with st.spinner("Thinking... (usually 5-20 seconds)"):
            try:
                if st.session_state.vector_store and use_pdf:
                    # Lightweight RAG
                    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": 2})
                    relevant_docs = retriever.invoke(prompt)
                    context = "\n\n".join([doc.page_content for doc in relevant_docs])[:3000]

                    full_prompt = f"""Context from PDF (use only if relevant):  
{context}

Question: {prompt}
Answer in simple {st.session_state.language}, encouraging way:"""

                    response = ollama.generate(model=MODEL, prompt=full_prompt, stream=True)
                    for chunk in response:
                        if 'response' in chunk:
                            full_response += chunk['response']
                            placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
                else:
                    # Normal fast chat
                    stream = ollama.chat(model=MODEL, messages=st.session_state.messages, stream=True)
                    for chunk in stream:
                        if 'message' in chunk and 'content' in chunk['message']:
                            full_response += chunk['message']['content']
                            placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)

            except Exception as e:
                st.error(f"Response error: {str(e)}\n1. Is 'ollama serve' running?\n2. Model pulled? Try simple question without PDF.")
                full_response = "Sorry yaar, kuch gadbad ho gayi. Try again or without PDF."

    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})

st.caption("Pro Tip: Small PDFs = faster answers | Try without PDF first if slow")