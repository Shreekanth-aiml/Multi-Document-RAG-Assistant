
import streamlit as st

from rag_pipeline import (
    create_vector_database,
    save_vector_database,
    ask_question,
    load_vector_database
)

st.set_page_config(
    page_title="RAG Import Test",
    page_icon="📚"
)

st.title("Multi-Document RAG Assistant")

st.success("All RAG modules imported successfully!")
