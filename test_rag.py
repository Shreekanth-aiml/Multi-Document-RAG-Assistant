from rag_pipeline import load_vector_database, ask_question

# Load the existing FAISS database
vector_database = load_vector_database()

# Ask a question about the PDFs
question = "What are the common data types in Python?"
# Generate an answer using RAG
answer = ask_question(vector_database, question)

print("\nAI Answer:")
print(answer)