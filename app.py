import streamlit as st
from chatbot.response_generator import generate_response
from chatbot.query_handler import find_relevant_image
from deep_translator import GoogleTranslator

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

def display_chat_history():
    """Displays past messages."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image_url" in message:
                st.image(message["image_url"], caption="Relevant Image")

def handle_user_input(prompt):
    """Processes user input and retrieves AI response & images."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = generate_response(prompt)
            translated_response = GoogleTranslator(source='auto', target='ja').translate(response_text)
            image_url = find_relevant_image(prompt)

            response_message = {"role": "assistant", "content": translated_response}
            if image_url:
                response_message["image_url"] = image_url

            st.session_state.messages.append(response_message)
            st.markdown(translated_response)

            if image_url:
                st.write(f"Debug: Image URL - {image_url}")  # Print the URL for debugging
                st.image(image_url, caption="Relevant Image")

# Streamlit UI
st.set_page_config(page_title="Archibus AI", layout="wide")
st.title("Archibus AI")
st.markdown("Welcome to Archibus AI")

display_chat_history()

if prompt := st.chat_input("Ask me anything..."):
    handle_user_input(prompt)
