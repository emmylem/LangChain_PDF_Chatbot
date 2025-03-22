import streamlit as st
import requests
import time

st.set_page_config(page_title="Forex Chatbot 💬", page_icon="💹", layout="wide")

st.markdown("""
    <style>
        .chat-container {
            max-width: 700px;
            margin: auto;
        }
        .message {
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
            max-width: 80%;
        }
        .user-message {
            background-color: #0078ff;
            color: white;
            align-self: flex-end;
            margin-left: auto;
        }
        .bot-message {
            background-color: #f3f3f3;
            color: black;
            align-self: flex-start;
            margin-right: auto;
        }
        .chat-box {
            display: flex;
            flex-direction: column;
        }
        .sidebar-title {
            font-size: 1.2em;
            font-weight: bold;
        }
        .sidebar-chat {
            cursor: pointer;
            padding: 8px;
            margin-bottom: 5px;
            border-radius: 5px;
            background-color: #f0f0f0;
            text-align: center;
        }
        .sidebar-chat:hover {
            background-color: #d0d0d0;
        }
        .new-chat {
            background-color: #0078ff;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 10px;
            width: 100%;
        }
        .new-chat:hover {
            background-color: #005bbb;
        }
    </style>
""", unsafe_allow_html=True)

st.title("💬 Forex Chatbot")

if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {}

st.sidebar.markdown('<p class="sidebar-title">📜 Chat History</p>', unsafe_allow_html=True)

if st.sidebar.button("➕ New Chat"):
    new_chat_id = str(len(st.session_state.chat_sessions) + 1)
    st.session_state.chat_sessions[new_chat_id] = []
    st.session_state.chat_titles[new_chat_id] = "New Chat"
    st.session_state.current_chat_id = new_chat_id
    st.rerun()

for chat_id, messages in st.session_state.chat_sessions.items():
    if messages:
        first_message = messages[0]["text"][:30] + "..." if len(messages[0]["text"]) > 30 else messages[0]["text"]
        st.session_state.chat_titles[chat_id] = first_message
    else:
        st.session_state.chat_titles[chat_id] = "New Chat"

    if st.sidebar.button(f"📌 {st.session_state.chat_titles[chat_id]}", key=chat_id):
        st.session_state.current_chat_id = chat_id
        st.rerun()

if st.session_state.current_chat_id is None:
    st.warning("Start a new chat or select an existing one from the sidebar.")
    st.stop()

chat_id = st.session_state.current_chat_id
chat_history = st.session_state.chat_sessions[chat_id]

chat_container = st.container()
with chat_container:
    for msg in chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="message user-message">{msg["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="message bot-message">{msg["text"]}</div>', unsafe_allow_html=True)

user_input = st.text_input("Type your message...", key="user_input", placeholder="Ask me about forex trends, currency pairs, etc.", label_visibility="collapsed")

if st.button("Send 🚀"):
    if user_input.strip():
        chat_history.append({"role": "user", "text": user_input})

        if len(chat_history) == 1:
            st.session_state.chat_titles[chat_id] = user_input[:30] + "..." if len(user_input) > 30 else user_input

        with st.spinner("Thinking..."):
            time.sleep(1)
            response = requests.post("http://127.0.0.1:5000/query", json={"question": user_input})

        if response.status_code == 200:
            bot_reply = response.json().get("response", "No response from server.")
        else:
            bot_reply = "⚠️ Error fetching response!"

        chat_history.append({"role": "bot", "text": bot_reply})
        st.session_state.chat_sessions[chat_id] = chat_history
        st.rerun()