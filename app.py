import os
import json
import streamlit as st
import google.generativeai as genai

# Path to the image mapping JSON
mapping_file = "C:\\Users\\Aryan\\Documents\\Archibus Docs\\Extracted\\s3_image_mapping.json"

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

# Base system instruction
base_instruction = """
You are a professional AI assistant for Archibus.
Your name is Archibus AI.
Please answer user questions according to the following rules:

1. Questions related to Archibus: Explain specific functions and operation methods
2. Facility management, maintenance, and cost data: Provide accurate analysis and guidance
3. Workflow automation: Change appropriate data based on command input
4. Integration functions (Slack, Teams, Email): Explain how to link
5. Learning ability: Utilize past question history to provide more appropriate answers

Always answer concisely and accurately, and speak in Japanese.
"""

# Load custom instruction from file
with open("Data.txt", "r") as file:
    custom_instruction = file.read().strip()

# Combine static system instruction with custom instruction
full_instruction = f"{base_instruction}\n\n{custom_instruction}"

# Store in session state
if "custom_instruction" not in st.session_state:
    st.session_state.custom_instruction = full_instruction

# Create the model instance
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction=st.session_state.custom_instruction,
)

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to find relevant image from mapping
def find_relevant_image(prompt):
    """Search for the most relevant image in the stored mapping based on prompt keywords."""
    keywords = prompt.lower().split()
    for local_path, s3_url in image_mapping.items():
        if any(keyword in local_path.lower() for keyword in keywords):
            return s3_url
    return None  # No relevant image found

# Function to display chat history
def display_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image_url" in message:
                st.image(message["image_url"], caption="Relevant Image")

# Function to handle user input and get response
def handle_user_input(prompt: str):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            conversation_history = [{"role": msg["role"], "parts": [msg["content"]]} for msg in st.session_state.messages]

            try:
                # Start chat with AI
                chat_session = model.start_chat(history=conversation_history)
                response = chat_session.send_message(prompt)

                # Check for relevant image
                image_url = find_relevant_image(prompt)

                # Store and display assistant response
                response_message = {"role": "assistant", "content": response.text}
                if image_url:
                    response_message["image_url"] = image_url  # Add image URL if found

                st.session_state.messages.append(response_message)
                st.markdown(response.text)
                if image_url:
                    st.image(image_url, caption="Relevant Image")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.messages.append({"role": "assistant", "content": "Sorry, an error occurred."})

# Main Streamlit App
def main():
    st.set_page_config(page_title="Archibus AI", layout="wide")
    st.title("Archibus AI")
    st.markdown("Welcome to Archibus AI")

    # Display chat history
    display_chat_history()

    # Handle user input
    if prompt := st.chat_input("Ask me anything..."):
        handle_user_input(prompt)

if __name__ == "__main__":
    main()
