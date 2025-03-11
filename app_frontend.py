import streamlit as st
import requests

st.title("📄 PDF Chatbot")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
if uploaded_file:
    files = {"file": uploaded_file}  # Streamlit automatically handles file upload correctly
    response = requests.post("http://127.0.0.1:5000/upload", files=files)
    
    if response.status_code == 200:
        st.success("✅ PDF uploaded and processed successfully!")
    else:
        st.error(f"❌ Upload failed: {response.json()}")

question = st.text_input("Ask a question:")
if question:
    response = requests.post("http://127.0.0.1:5000/ask", json={"question": question})
    
    if response.status_code == 200:
        st.write("💬 **Answer:**", response.json().get("answer", "No response"))
    else:
        st.error("❌ Error fetching response from the backend.")
