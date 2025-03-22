import streamlit as st
from chatbot.response_generator import generate_response
from chatbot.query_handler import find_relevant_images

st.set_page_config(page_title="Archibus AI", layout="wide")

# ✅ Custom Navbar with Deploy & Language Dropdown
st.markdown(
    """
    <style>
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1.5rem;
            background-color: #121212;
            color: white;
            border-bottom: 1px solid #333;
        }
        .navbar-right {
            display: flex;
            align-items: center;
        }
        .dropdown {
            background: #1e1e1e;
            border: 1px solid #444;
            padding: 5px;
            border-radius: 5px;
            color: white;
            margin-left: 10px;
            cursor: pointer;
        }
    </style>
    <div class="navbar">
        <span style="font-size: 20px; font-weight: bold;">Archibus AI</span>
        <div class="navbar-right">
            <span>Selected Language</span>
            <select class="dropdown" id="language" onchange="setLanguage(this.value)">
                <option value="Japanese">Japanese</option>
                <option value="English">English</option>
            </select>
        </div>
    </div>
    
    <script>
        function setLanguage(lang) {
            fetch("/set_language?lang=" + lang)
            .then(response => response.json())
            .then(data => console.log("Language Set:", data));
        }
    </script>
    """,
    unsafe_allow_html=True
)

# ✅ Handle Language Selection in Session State
if "language" not in st.session_state:
    st.session_state.language = "Japanese"

# ✅ Sidebar UI (New Chat & Search Button)
st.sidebar.title("Settings")

col1, col2 = st.sidebar.columns([0.2, 0.8])

with col1:
    if st.button("➕"):
        st.session_state.messages = []  # New chat

with col2:
    if st.button("🔍"):
        st.warning("Search functionality is not yet implemented.")

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
    """Processes user input and retrieves AI response & multiple images in order."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = generate_response(prompt, st.session_state.language)

            # Fetch ordered images (Step 1 → Step 2 → Step 3)
            image_urls = find_relevant_images(prompt, top_k=5)  

            response_message = {"role": "assistant", "content": response_text}
            if image_urls:
                response_message["image_urls"] = list(dict.fromkeys(image_urls))  # Remove duplicates
            
            st.session_state.messages.append(response_message)
            st.markdown(response_text)

            if image_urls:
                st.write(f" **Retrieved {len(image_urls)} images:**")
                for idx, img_url in enumerate(image_urls, start=1):
                    st.image(img_url, caption=f"Image {idx}")

# Streamlit UI
st.title("Archibus AI")
st.markdown("Welcome to Archibus AI")

display_chat_history()

if prompt := st.chat_input("Ask me anything..."):
    handle_user_input(prompt)