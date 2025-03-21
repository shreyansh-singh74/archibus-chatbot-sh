import streamlit as st
from chatbot.response_generator import generate_response
from chatbot.query_handler import find_relevant_images

def is_complex_query(query):
    """Detects if a query is complex based on keywords and length."""
    keywords = ["features", "setup", "configuration", "troubleshooting", "offline mode", "workflow", "integration"]
    return any(keyword in query.lower() for keyword in keywords) or len(query.split()) > 8

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

def display_chat_history():
    """Displays past messages and retrieved images."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image_urls" in message:
                for img_url in message["image_urls"]:
                    st.image(img_url, caption="Relevant Image")

def handle_user_input(prompt):
    """Processes user input and retrieves AI response & multiple images."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = generate_response(prompt)

            # Fetch images for all queries (not just complex ones)
            image_urls = find_relevant_images(prompt, top_k=5)  # Retrieve multiple images

            response_message = {"role": "assistant", "content": response_text}
            if image_urls:
                response_message["image_urls"] = image_urls  # Store multiple images
            
            st.session_state.messages.append(response_message)
            st.markdown(response_text)

            if image_urls:
                st.write(f"Debug: Retrieved {len(image_urls)} images")
                for img_url in image_urls:
                    st.image(img_url, caption="Relevant Image")

# Streamlit UI
st.set_page_config(page_title="Archibus AI", layout="wide")
st.title("Archibus AI")
st.markdown("Welcome to Archibus AI")

display_chat_history()

if prompt := st.chat_input("Ask me anything..."):
    handle_user_input(prompt)
