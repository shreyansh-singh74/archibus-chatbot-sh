import google.generativeai as genai
import streamlit as st

API_KEY = "AIzaSyAuQOFtD6OQe_iDyPcKftGEJ5LbToJyZK8"

# Configure Generative AI
genai.configure(api_key=API_KEY)

# AI Model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    generation_config=generation_config
)

def generate_response(prompt):
    """Generates AI response based on prompt."""
    chat_session = model.start_chat(history=[{"role": "user", "parts": [prompt]}])
    response = chat_session.send_message(prompt)
    return response.text
