import streamlit as st
from utils.faiss_store import FAISSDocumentStore
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import fitz 
from PIL import Image
from io import BytesIO
import os

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAuQOFtD6OQe_iDyPcKftGEJ5LbToJyZK8"
genai.configure(api_key=GEMINI_API_KEY)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Define paths for FAISS
index_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_index.idx")
metadata_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_metadata.pkl")

# Create data directory if it doesn't exist
os.makedirs(os.path.dirname(index_path), exist_ok=True)

if "faiss_store" not in st.session_state:
    st.session_state.faiss_store = FAISSDocumentStore(
        index_path=index_path if os.path.exists(index_path) else None,
        metadata_path=metadata_path if os.path.exists(metadata_path) else None
    )
    
# For API compatibility with previous ChromaDB code
if "collection" not in st.session_state:
    st.session_state.collection = st.session_state.faiss_store

if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None 

if "extracted_images" not in st.session_state:
    st.session_state.extracted_images = {}

def extract_images_from_pdf(pdf_file):
    pdf_file.seek(0)  
    pdf_reader = fitz.open(stream=pdf_file.read(), filetype="pdf")  
    images = {}
    for page_num, page in enumerate(pdf_reader.pages(), start=1):
        img_list = page.get_images(full=True)
        page_images = []
        for img in img_list:
            xref = img[0]
            base_image = pdf_reader.extract_image(xref)
            image_bytes = base_image["image"]
            page_images.append(image_bytes)
        if page_images:
            images[page_num] = page_images
    return images

def upload_and_embed_pdf(pdf_file):
    if pdf_file.name in st.session_state.processed_files:
        st.warning(f"⚠️ {pdf_file.name} is already processed.")
        return

    with st.status("🔍 Analyzing your document...", expanded=True) as status:
        st.write("Extracting text and images...")
        pdf_reader = PdfReader(pdf_file)
        images = extract_images_from_pdf(pdf_file)
        st.session_state.extracted_images[pdf_file.name] = images

        documents = []
        embeddings = []
        ids = []

        for page_num, page in enumerate(pdf_reader.pages, start=1):
            text = page.extract_text()
            if text:
                embedding = embedding_model.encode(text).tolist()  
                embedding_id = f"{pdf_file.name}_{page_num}"
                
                documents.append(text)
                embeddings.append(embedding)
                ids.append(embedding_id)
                
                st.write(f"Added embedding for page {page_num} with ID {embedding_id}")  
        
        # Add all embeddings at once for better performance
        if documents:
            st.session_state.collection.add(
                documents=documents,
                embeddings=embeddings,
                ids=ids,
            )
            
            # Save the updated index and metadata
            st.session_state.faiss_store.save(index_path, metadata_path)
        
        status.update(label="✅ Document analyzed successfully!", state="complete", expanded=False)

    st.session_state.processed_files.add(pdf_file.name)
    st.session_state.uploaded_file = pdf_file.name 

def remove_document():
    if st.session_state.uploaded_file:
        doc_ids = [f"{st.session_state.uploaded_file}_{i}" for i in range(1000)]  
        st.session_state.collection.delete(ids=doc_ids)
        
        # Save the updated index and metadata
        st.session_state.faiss_store.save(index_path, metadata_path)
        
        st.session_state.processed_files.discard(st.session_state.uploaded_file)
        st.session_state.uploaded_file = None
        st.session_state.extracted_images.pop(st.session_state.uploaded_file, None)
        st.success("🗑 Document removed successfully!")

def get_images_for_page(page_number):
    if st.session_state.uploaded_file:
        return st.session_state.extracted_images.get(st.session_state.uploaded_file, {}).get(page_number, [])
    return []

def display_images_gallery(images_for_page):
    if images_for_page:
        cols = st.columns(len(images_for_page))  
        for idx, img_bytes in enumerate(images_for_page):
            image = Image.open(BytesIO(img_bytes))  
            with cols[idx]:  
                st.image(image, caption=f"Image {idx + 1}", use_container_width=True)
    else:
        st.write("🔍 No images found for this page.")

def chat_with_gemini(query):
    query_embedding = embedding_model.encode(query).tolist()
    closest_pages = st.session_state.collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    if not closest_pages["documents"] or len(closest_pages["documents"][0]) == 0:
        return "No relevant context found. Try rephrasing your question!", None

    context = "\n".join(closest_pages["documents"][0])
    document_id_list = closest_pages["ids"]
    if isinstance(document_id_list, list) and isinstance(document_id_list[0], list):
        document_id = document_id_list[0][0] 
        document_id_parts = document_id.split('_')
        page_number = int(document_id_parts[-1])  
    else:
        st.error("❌ Unexpected document ID format.")
        return "❌ Unexpected document ID format.", None

    images_for_page = get_images_for_page(page_number)

    with st.spinner("🤖 Generating response..."):
        model = genai.GenerativeModel("gemini-2.0-flash")  # Use Gemini model
        response = model.generate_content(f"Context:\n{context}\n\nQuestion: {query}")

    return response.text, images_for_page

st.set_page_config(page_title="Chatbot with Document Upload (FAISS-Based)", layout="wide")
st.title("📄💬 AI Chatbot with FAISS Document Search")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"], help="Upload your document to start chatting with it.")
if uploaded_file:
    upload_and_embed_pdf(uploaded_file)

if "uploaded_file" in st.session_state and st.session_state.uploaded_file:
    st.write(f"📄 {st.session_state.uploaded_file} analyzed and ready for queries!")
    if st.button("❌ Remove Document"):
        remove_document()

user_query = st.text_input("Ask something about the document:")
if user_query:
    st.write("🤖 AI Response:")
    response_text, images_for_page = chat_with_gemini(user_query)
    st.write(response_text)
    display_images_gallery(images_for_page)