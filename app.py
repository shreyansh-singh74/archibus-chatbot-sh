import os
import json
import streamlit as st
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Path to the image mapping JSON
mapping_file = r"C:\Users\vivek gupta\OneDrive\Desktop\archibus\archibus-chatbot\s3_image_mapping.json"

# Load pre-stored S3 image mapping
if os.path.exists(mapping_file):
    with open(mapping_file, "r") as f:
        image_mapping = json.load(f)
else:
    st.error("Image mapping file not found! Please ensure images are uploaded and mapped correctly.")
    image_mapping = {}

# Load API key for Gemini AI
api_key = st.secrets['defaults']['GOOGLE_API_KEY']
genai.configure(api_key=api_key)

# Define generation parameters
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Load and preprocess Data.txt for RAG
data_file = "Data.txt"
if os.path.exists(data_file):
    with open(data_file, "r", encoding='utf-8') as file:
        text = file.read()
    chunks = [s.strip() for s in text.split('\n\n') if len(s.strip()) > 50]
    model_embed = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model_embed.encode(chunks, convert_to_numpy=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
else:
    st.warning("Data.txt not found. Running without custom data for now.")
    chunks = ["No data available yet."]
    model_embed = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model_embed.encode(chunks, convert_to_numpy=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

# Base system instruction
base_instruction = """
You are a professional AI assistant for Archibus named Archibus AI.
Answer concisely and only with information relevant to the user’s question.
Do not repeat or dump entire sections of data—summarize or extract key points.
1. For Archibus questions: Explain functions and operations.
2. For facility management, maintenance, or cost data: Provide analysis and guidance.
3. For workflow automation: Adjust data based on input.
4. For integrations (Slack, Teams, Email): Explain linking steps.
5. Use past question history to improve answers.
6. Respond in Japanese, keeping it professional and clear.
"""

# Store in session state
if "custom_instruction" not in st.session_state:
    st.session_state.custom_instruction = base_instruction

# Create the model instance
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction=st.session_state.custom_instruction,
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Find relevant image from mapping (still kept for pre-existing S3 mapping)
def find_relevant_image(prompt):
    keywords = prompt.lower().split()
    for local_path, s3_url in image_mapping.items():
        if any(keyword in local_path.lower() for keyword in keywords):
            return s3_url
    return None

# Get relevant chunks from Data.txt
def get_relevant_chunks(prompt):
    query_embedding = model_embed.encode([prompt])
    distances, indices = index.search(query_embedding, k=5)
    return "\n".join([chunks[i] for i in indices[0]])

# Display chat history
def display_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image_url" in message:
                st.image(message["image_url"], caption="Relevant Image")

# Handle user input (no image upload)
def handle_user_input(prompt: str):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            conversation_history = [{"role": msg["role"], "parts": [msg["content"]]} for msg in st.session_state.messages]
            relevant_context = get_relevant_chunks(prompt)
            full_prompt = f"Context: {relevant_context}\n\nQuestion: {prompt}"

            try:
                chat_session = model.start_chat(history=conversation_history)
                response = chat_session.send_message(full_prompt)

                image_url = find_relevant_image(prompt)
                response_message = {"role": "assistant", "content": response.text}
                if image_url:
                    response_message["image_url"] = image_url
                st.session_state.messages.append(response_message)
                st.markdown(response.text)
                if image_url:
                    st.image(image_url, caption="Relevant Image")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.messages.append({"role": "assistant", "content": "Sorry, an error occurred."})

# Main app
def main():
    st.set_page_config(page_title="Archibus AI", layout="wide")
    st.title("Archibus AI")
    st.markdown("Welcome to Archibus AI")

    display_chat_history()

    if prompt := st.chat_input("Ask me anything..."):
        handle_user_input(prompt)

if __name__ == "__main__":
    main()