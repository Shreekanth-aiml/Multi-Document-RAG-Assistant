
import os

from langchain_community.vectorstores import FAISS

from document_processor import (
    extract_text_from_pdf,
    split_text_into_chunks
)

from embedding_processor import create_embedding_model
from llm_processor import generate_response


# Retrieval settings
TOP_K = 5
FETCH_K = 15
MMR_LAMBDA = 0.7

UNAVAILABLE_MESSAGE = (
    "This information is not available in the uploaded documents."
)


# Step 1: Find PDF files
def get_pdf_files(folder_path):

    if not os.path.exists(folder_path):
        raise FileNotFoundError(
            f"Folder not found: {folder_path}"
        )

    return [
        os.path.join(folder_path, file)
        for file in os.listdir(folder_path)
        if file.lower().endswith(".pdf")
    ]


# Step 2: Create FAISS database
def create_vector_database(folder_path):

    pdf_files = get_pdf_files(folder_path)

    if not pdf_files:
        raise ValueError(
            f"No PDF files found in {folder_path}"
        )

    all_chunks = []

    for pdf_path in pdf_files:

        print(f"Processing: {pdf_path}")

        pages = extract_text_from_pdf(pdf_path)

        chunks = split_text_into_chunks(pages)

        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError(
            "No text could be extracted from PDF files."
        )

    texts = [
        chunk["text"] for chunk in all_chunks
    ]

    metadatas = [
        {
            "source": chunk["source"],
            "page": chunk["page"]
        }
        for chunk in all_chunks
    ]

    embedding_model = create_embedding_model()

    vector_database = FAISS.from_texts(
        texts,
        embedding_model,
        metadatas=metadatas
    )

    print(f"Total PDF files: {len(pdf_files)}")
    print(f"Total chunks: {len(all_chunks)}")

    return vector_database


# Step 3: Retrieve relevant document chunks
def search_similar_chunks(vector_database, question):

    results = vector_database.max_marginal_relevance_search(
        question,
        k=TOP_K,
        fetch_k=FETCH_K,
        lambda_mult=MMR_LAMBDA
    )

    return results


# Step 4: Save FAISS database
def save_vector_database(vector_database):

    os.makedirs(
        "vectorstore/faiss_index",
        exist_ok=True
    )

    vector_database.save_local(
        "vectorstore/faiss_index"
    )

    print("Vector database saved successfully!")


# Step 5: Load FAISS database
def load_vector_database():

    embedding_model = create_embedding_model()

    return FAISS.load_local(
        "vectorstore/faiss_index",
        embedding_model,
        allow_dangerous_deserialization=True
    )


# Step 6: Rewrite follow-up questions
def rewrite_question(question, chat_history):

    if not chat_history:
        return question

    recent_history = chat_history[-4:]

    conversation_history = ""

    for chat in recent_history:

        conversation_history += (
            f"\nUser: {chat['question']}\n"
            f"Assistant: {chat['answer']}\n"
        )

    prompt = f"""
You rewrite questions for a document search system.

Use the previous conversation to understand the latest question.

Rules:
1. Rewrite the latest question as a standalone question.
2. Keep its original meaning.
3. Do not answer the question.
4. Do not add information that was not discussed.
5. Return only the rewritten question.

Previous conversation:
{conversation_history}

Latest question:
{question}

Standalone question:
"""

    rewritten_question = generate_response(prompt).strip()

    if not rewritten_question:
        return question

    return rewritten_question


# Step 7: Prepare retrieved context and sources
def prepare_context(results):

    context = ""
    sources = []

    for index, result in enumerate(results, start=1):

        document_name = os.path.basename(
            result.metadata.get("source", "Unknown document")
        )

        page_number = result.metadata.get(
            "page",
            "Unknown"
        )

        source = {
            "source_id": index,
            "document": document_name,
            "page": page_number,
            "content": result.page_content
        }

        sources.append(source)

        context += f"""
[Source {index}]
Document: {document_name}
Page: {page_number}
Content:
{result.page_content}

"""

    return context, sources


# Step 8: Generate grounded answer
def generate_grounded_answer(question, context, conversation_history):

    prompt = f"""
You are a reliable multi-document question-answering assistant.

Answer the user's question using ONLY the retrieved document context.

STRICT RULES:

1. Do not use outside knowledge.
2. Do not invent facts, numbers, or examples.
3. If the context does not contain the answer, say:
   "{UNAVAILABLE_MESSAGE}"
4. Use simple and clear English.
5. Organize the answer with headings or bullet points when useful.
6. Support factual claims with citations such as [Source 1].
7. Use only the source numbers provided in the context.
8. If multiple documents support the answer, cite the relevant sources.
9. Do not create fake document names or page numbers.
10. Previous conversation is only for understanding the question.
    It is not evidence for answering.

Previous conversation:
{conversation_history}

Retrieved document context:
{context}

Current question:
{question}

Answer:
"""

    return generate_response(prompt)


# Step 9: Main question-answering function
def ask_question(vector_database, question, chat_history=None):

    if chat_history is None:
        chat_history = []

    # Rewrite follow-up questions
    search_question = rewrite_question(
        question,
        chat_history
    )

    # Retrieve relevant chunks
    results = search_similar_chunks(
        vector_database,
        search_question
    )

    if not results:

        return {
            "answer": UNAVAILABLE_MESSAGE,
            "sources": []
        }

    # Prepare context and source details
    context, sources = prepare_context(results)

    if not context.strip():

        return {
            "answer": UNAVAILABLE_MESSAGE,
            "sources": []
        }

    # Prepare recent conversation history
    recent_history = chat_history[-4:]

    conversation_history = ""

    for chat in recent_history:

        conversation_history += (
            f"\nUser: {chat['question']}\n"
            f"Assistant: {chat['answer']}\n"
        )

    # Generate answer
    answer = generate_grounded_answer(
        question,
        context,
        conversation_history
    )

    return {
        "answer": answer,
        "sources": sources
    }
