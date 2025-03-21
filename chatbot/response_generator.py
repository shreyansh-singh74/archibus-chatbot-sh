import google.generativeai as genai
import os

API_KEY = "AIzaSyAuQOFtD6OQe_iDyPcKftGEJ5LbToJyZK8"

# Configure Generative AI
genai.configure(api_key=API_KEY)

# AI Model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config
)

# Base Instruction (Japanese)
BASE_INSTRUCTION = """
You are a professional AI assistant for Archibus.
Your name is Archibus AI.
Please answer user questions according to the following rules:

1. Questions related to Archibus: Explain specific functions and operation methods **in detail**.
2. Facility management, maintenance, and cost data: Provide **comprehensive** analysis and guidance.
3. Workflow automation: Change appropriate data based on command input **and provide clear explanations**.
4. Integration functions (Slack, Teams, Email): Explain how to link **step by step**.
5. Learning ability: Utilize past question history to provide more appropriate answers.

Always answer **thoroughly yet structured**, and speak in Japanese.
"""


# Load additional instructions from Data.txt
data_file_path = "D:\\ArchiBusV2\\Data.txt"

if os.path.exists(data_file_path):
    with open(data_file_path, "r", encoding="utf-8") as file:
        additional_instructions = file.read().strip()
else:
    additional_instructions = ""

# Combine static system instruction with custom instruction
FULL_INSTRUCTION = f"{BASE_INSTRUCTION}\n\n{additional_instructions}"

def generate_response(prompt):
    """Generates AI response based on prompt with base + custom instruction."""
    full_prompt = f"{FULL_INSTRUCTION}\n\nUser Question (Provide a detailed response): {prompt}"

    
    chat_session = model.start_chat(history=[{"role": "user", "parts": [full_prompt]}])
    response = chat_session.send_message(full_prompt)
    
    return response.text
