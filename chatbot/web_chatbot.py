import streamlit as st
import sys, os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.langgraph_workflow import run_agent

st.set_page_config(page_title="Faculty AI Chatbot", page_icon="🤖")

# Custom CSS for a clean chatbot look
st.markdown("""
<style>
    .stApp {
        background: #0f172a;
        color: #f1f5f9;
    }
    .chat-bubble-user {
        background: rgba(124, 58, 237, 0.2);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .chat-bubble-ai {
        background: rgba(6, 182, 212, 0.15);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Faculty AI Assistant")
st.write("Ask me anything about faculty performance, KPI insights, or strategic recommendations.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What is the average performance score in CSE?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Default to Principal role for broad queries in standalone mode
            response = run_agent(query=prompt, role="Principal")
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
