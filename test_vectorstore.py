from rag_pipeline import load_vector_database, search_similar_chunks

# Load FAISS database
vector_database = load_vector_database()

print("FAISS database loaded successfully!")

# Ask a question
question = "What is the document about?"

# Retrieve relevant chunks
results = search_similar_chunks(vector_database, question)

print("\nSearch Results:")

for i, result in enumerate(results, start=1):

    print(f"\nResult {i}:")
    print("Source:", result.metadata["source"])
    print("Page:", result.metadata["page"])
    print("Content:", result.page_content)