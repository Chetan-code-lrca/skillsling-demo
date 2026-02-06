import streamlit as st
from ollama import Client

# Title and intro
st.title("SkillSling – Your Offline AI Tutor")
st.markdown("Ask doubts in Hindi or English. 100% local, no internet needed after setup! 🚀")

# Connect to your local Ollama
client = Client()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Type your doubt (e.g., 'Projectile motion range formula kya hai?' or class 10 science question)"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # System prompt for clean responses
    system_prompt = {
        "role": "system",
        "content": "You are a helpful teacher for school students. Answer in simple, clean Hindi or English only. Keep answers short, clear, and accurate. Use bullet points for lists. No repetition."
    }

    # Build full message list with history + system prompt
    full_messages = [system_prompt] + st.session_state.messages

    # Generate response with streaming (shows typing effect)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        stream_response = client.chat(
            model='gemma3:4b',
            messages=full_messages,
            stream=True,
        )

        for chunk in stream_response:
            if 'message' in chunk and 'content' in chunk['message']:
                content = chunk['message']['content']
                full_response += content
                message_placeholder.markdown(full_response + "▌")

        # Final response without cursor
        message_placeholder.markdown(full_response)

    # Save assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})