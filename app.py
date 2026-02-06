import streamlit as st
from ollama import Client

# ────────────────────────────────────────────────
# Title & Intro
# ────────────────────────────────────────────────
st.set_page_config(page_title="SkillSling", page_icon="🧠", layout="wide")

st.title("SkillSling – Your Offline AI Tutor")
st.markdown(
    "Ask any doubt in **Hindi** or **English**. Runs 100% locally on your laptop — "
    "no internet needed after setup! 🚀"
)

# ────────────────────────────────────────────────
# Connect to Ollama
# ────────────────────────────────────────────────
@st.cache_resource
def get_ollama_client():
    try:
        client = Client()
        # Quick test to see if Ollama is alive
        client.chat(model='gemma3:4b', messages=[{"role": "user", "content": "hi"}])
        return client
    except Exception as e:
        st.error("Ollama is not running or not reachable. Please start Ollama and load gemma3:4b first.")
        st.stop()

client = get_ollama_client()

# ────────────────────────────────────────────────
# Chat history
# ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Clear chat button
if st.button("Clear Chat", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

# Display chat history
for message in st.session_state.messages:
    avatar = "🧑‍🎓" if message["role"] == "user" else "🧠"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# ────────────────────────────────────────────────
# User input
# ────────────────────────────────────────────────
if prompt := st.chat_input("Type your doubt (e.g., 'Projectile motion range formula kya hai?' or class 10 science question)"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)

    # ────────────────────────────────────────────────
    # Strong system prompt (this makes the biggest difference!)
    # ────────────────────────────────────────────────
    system_prompt = {
    "role": "system",
    "content": """You are a very clear teacher for Indian students. 
Reply ONLY in the exact language the user asked in (Telugu, Hindi or English).
Keep EVERY answer SHORT (max 100 words), clean, accurate and well-structured.
Use bullet points for lists, steps or definitions.
NEVER repeat any sentence, word or idea — be extremely concise.
Use simple, correct words only — no broken or mixed text.
If the question is in Telugu, write perfect, natural Telugu only.
Always end with one short check question like "అర్థమైందా?" or "Got it?"."""
}

    # Build full message list (system prompt + history)
    full_messages = [system_prompt] + st.session_state.messages

    # ────────────────────────────────────────────────
    # Generate response with streaming
    # ────────────────────────────────────────────────
    with st.chat_message("assistant", avatar="🧠"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            stream_response = client.chat(
    model='gemma3:4b',
    messages=full_messages,
    stream=True,
    options={
        "temperature": 0.5,       # much lower = less randomness & repetition
        "top_p": 0.75,            # tighter nucleus sampling
        "top_k": 30,              # limits token choices
        "repeat_penalty": 1.2     # strongly discourages repetition
    }
)

            for chunk in stream_response:
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")

            # Final clean response
            message_placeholder.markdown(full_response)

            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Error connecting to Ollama: {str(e)}\nMake sure Ollama is running and model is loaded.")
