import os
import fitz  # PyMuPDF
import chromadb
import requests
from flask import Flask, request, jsonify
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import HuggingFaceHub
from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

app = Flask(__name__)

# Initialize ChromaDB for vector storage
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_model = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2"
)  

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text("text") for page in doc)
    return text


def store_pdf_in_vector_db(pdf_text):
    """Store extracted PDF text as embeddings"""
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(pdf_text)

    vector_db = Chroma(
        persist_directory="./chroma_db", embedding_function=embedding_model
    )
    vector_db.add_texts(texts)
    return vector_db


@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save file temporarily
    pdf_path = os.path.join("uploads", file.filename)
    file.save(pdf_path)

    # Extract text and store in vector DB
    pdf_text = extract_text_from_pdf(pdf_path)
    vector_db = store_pdf_in_vector_db(pdf_text)

    return jsonify({"message": "PDF processed successfully"}), 200


@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Load stored embeddings
    vector_db = Chroma(
        persist_directory="./chroma_db", embedding_function=embedding_model
    )

    retriever = vector_db.as_retriever()

    # 🔹 Retrieve relevant document chunks
    retrieved_docs = retriever.get_relevant_documents(question)
    retrieved_text = "\n".join([doc.page_content for doc in retrieved_docs])

    # 🔹 Send retrieved text + user question to Mistral API
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistral-tiny",
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant. Use the provided document context to answer the user's question.",
            },
            {
                "role": "user",
                "content": f"Document context:\n{retrieved_text}\n\nQuestion: {question}",
            },
        ],
    }

    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload
    )

    if response.status_code == 200:
        answer = (
            response.json()
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No response")
        )
        return jsonify({"answer": answer})
    else:
        return (
            jsonify(
                {
                    "error": "Failed to get response from Mistral API",
                    "details": response.text,
                }
            ),
            500,
        )


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
