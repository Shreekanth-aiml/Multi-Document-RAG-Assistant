
import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Load local environment variables
load_dotenv()

# First, check the local environment
api_key = os.getenv("GROQ_API_KEY")

# If not found, check Streamlit Cloud Secrets
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = None

# Validate API key
if not api_key:
    raise ValueError(
        "GROQ_API_KEY is missing. Add it to .env or Streamlit Secrets."
    )

# Remove accidental spaces
api_key = api_key.strip()

# Create Groq client
client = Groq(api_key=api_key)


def generate_response(prompt):

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="openai/gpt-oss-20b"
    )

    response = chat_completion.choices[0].message.content

    return response
