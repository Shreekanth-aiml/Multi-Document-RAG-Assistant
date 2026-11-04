from embedding_processor import create_embedding_model

# Load the embedding model
embedding_model = create_embedding_model()

# Convert sample text into a numerical vector
text = "Python is a programming language."

vector = embedding_model.embed_query(text)

print("Embedding model loaded successfully!")
print("Vector length:", len(vector))
print("First 10 values:", vector[:10])
