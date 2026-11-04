
import os
import json
import shutil
import hashlib
import streamlit as st

from rag_pipeline import (
    create_vector_database,
    save_vector_database,
    ask_question,
    load_vector_database
)

from document_processor import (
    get_pdf_metadata,
    get_pdf_page_preview
)


# 1. Application configuration
st.set_page_config(
    page_title="Multi-Document RAG Assistant",
    page_icon="📚",
    layout="wide"
)

CHAT_HISTORY_FILE = "chat_history.json"
DATA_FOLDER = "data"
VECTOR_FOLDER = "vectorstore/faiss_index"


# 2. Persistent chat memory
def load_chat_history():

    if not os.path.exists(CHAT_HISTORY_FILE):
        return []

    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)

        return history if isinstance(history, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def save_chat_history(history):

    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            history,
            file,
            indent=4,
            ensure_ascii=False
        )


# 3. Duplicate detection
def calculate_file_hash(file_content):

    return hashlib.sha256(file_content).hexdigest()


def get_existing_file_hashes():

    existing_hashes = set()

    if not os.path.exists(DATA_FOLDER):
        return existing_hashes

    for filename in os.listdir(DATA_FOLDER):

        if filename.lower().endswith(".pdf"):

            file_path = os.path.join(
                DATA_FOLDER,
                filename
            )

            with open(file_path, "rb") as file:
                file_hash = calculate_file_hash(file.read())

            existing_hashes.add(file_hash)

    return existing_hashes


def get_unique_filename(filename):

    base_name, extension = os.path.splitext(filename)

    file_path = os.path.join(
        DATA_FOLDER,
        filename
    )

    counter = 1

    while os.path.exists(file_path):

        new_name = f"{base_name}_{counter}{extension}"

        file_path = os.path.join(
            DATA_FOLDER,
            new_name
        )

        counter += 1

    return file_path


# 4. Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history()


# 5. Create data folder
os.makedirs(DATA_FOLDER, exist_ok=True)


# 6. Custom styling
st.markdown("""
<style>
    .main-title {
        font-size: 32px;
        font-weight: 700;
        color: #2563EB;
    }

    .subtitle {
        color: #64748B;
        font-size: 16px;
    }

    .stButton button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# 7. Application heading
st.markdown(
    '<div class="main-title">📚 Multi-Document RAG Assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Upload multiple PDFs and get intelligent answers using AI.</div>',
    unsafe_allow_html=True
)

st.divider()


# 8. Sidebar document manager
st.sidebar.title("📁 Document Manager")

pdf_files = [
    file for file in os.listdir(DATA_FOLDER)
    if file.lower().endswith(".pdf")
]

st.sidebar.subheader("Uploaded Documents")

if pdf_files:

    for pdf in pdf_files:
        st.sidebar.write(f"📄 {pdf}")

else:

    st.sidebar.info("No PDF documents uploaded yet.")


# 9. PDF metadata and page preview
st.sidebar.divider()

st.sidebar.subheader("📊 PDF Information")

if pdf_files:

    selected_preview_pdf = st.sidebar.selectbox(
        "Select PDF for information",
        pdf_files,
        key="metadata_pdf"
    )

    preview_path = os.path.join(
        DATA_FOLDER,
        selected_preview_pdf
    )

    try:

        metadata = get_pdf_metadata(preview_path)

        st.sidebar.write(
            f"**Filename:** {metadata['filename']}"
        )

        st.sidebar.write(
            f"**Total pages:** {metadata['total_pages']}"
        )

        st.sidebar.write(
            f"**File size:** {metadata['file_size_kb']} KB"
        )

        st.sidebar.subheader("📖 Page Preview")

        selected_page = st.sidebar.number_input(
            "Select page number",
            min_value=1,
            max_value=metadata["total_pages"],
            value=1,
            step=1
        )

        if st.sidebar.button(
            "Preview Page",
            use_container_width=True
        ):

            page_text = get_pdf_page_preview(
                preview_path,
                int(selected_page)
            )

            st.session_state["page_preview"] = {
                "document": selected_preview_pdf,
                "page": int(selected_page),
                "text": page_text
            }

    except Exception as error:

        st.sidebar.error(
            f"Unable to read PDF information: {error}"
        )


# 10. Upload PDF documents
st.sidebar.divider()

st.sidebar.subheader("Upload PDF Documents")

uploaded_files = st.sidebar.file_uploader(
    "Choose PDF files",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    if st.sidebar.button(
        "Process Documents",
        use_container_width=True
    ):

        added_files = []
        duplicate_files = []

        try:

            existing_hashes = get_existing_file_hashes()

            with st.spinner("Checking and processing PDFs..."):

                for uploaded_file in uploaded_files:

                    file_content = uploaded_file.getvalue()

                    file_hash = calculate_file_hash(
                        file_content
                    )

                    if file_hash in existing_hashes:

                        duplicate_files.append(
                            uploaded_file.name
                        )

                        continue

                    file_path = get_unique_filename(
                        os.path.basename(uploaded_file.name)
                    )

                    with open(file_path, "wb") as file:
                        file.write(file_content)

                    existing_hashes.add(file_hash)

                    added_files.append(
                        os.path.basename(file_path)
                    )

                if added_files:

                    vector_database = create_vector_database(
                        DATA_FOLDER
                    )

                    save_vector_database(vector_database)

            if added_files:

                st.sidebar.success(
                    f"Added {len(added_files)} new document(s)."
                )

            if duplicate_files:

                st.sidebar.warning(
                    "Skipped duplicates: "
                    + ", ".join(duplicate_files)
                )

            if not added_files and not duplicate_files:

                st.sidebar.info("No new files selected.")

            st.rerun()

        except Exception as error:

            st.sidebar.error(
                f"Processing error: {error}"
            )


# 11. Remove PDF documents
st.sidebar.divider()

if pdf_files:

    st.sidebar.subheader("Remove Document")

    selected_pdf = st.sidebar.selectbox(
        "Select document to remove",
        pdf_files,
        key="remove_pdf"
    )

    if st.sidebar.button(
        "Remove Selected Document",
        use_container_width=True
    ):

        try:

            os.remove(
                os.path.join(DATA_FOLDER, selected_pdf)
            )

            remaining_pdfs = [
                file for file in os.listdir(DATA_FOLDER)
                if file.lower().endswith(".pdf")
            ]

            if remaining_pdfs:

                with st.spinner("Updating vector database..."):

                    vector_database = create_vector_database(
                        DATA_FOLDER
                    )

                    save_vector_database(vector_database)

            else:

                if os.path.exists(VECTOR_FOLDER):
                    shutil.rmtree(VECTOR_FOLDER)

            st.sidebar.success(
                "Document removed successfully!"
            )

            st.rerun()

        except Exception as error:

            st.sidebar.error(
                f"Unable to remove document: {error}"
            )


# 12. Chat settings
st.sidebar.divider()

st.sidebar.subheader("Chat Settings")

if st.sidebar.button(
    "🗑️ Clear Chat History",
    use_container_width=True
):

    st.session_state.chat_history = []

    save_chat_history([])

    st.rerun()


# 13. Download chat history
if st.session_state.chat_history:

    chat_text = ""

    for chat in st.session_state.chat_history:

        chat_text += f"Question: {chat['question']}\n"
        chat_text += f"Answer: {chat['answer']}\n"

        chat_text += "\n" + "-" * 50 + "\n\n"

    st.sidebar.download_button(
        label="⬇️ Download Chat History",
        data=chat_text,
        file_name="chat_history.txt",
        mime="text/plain",
        use_container_width=True
    )


# 14. Dashboard statistics
col1, col2 = st.columns(2)

with col1:

    st.metric(
        "Uploaded PDF Documents",
        len(pdf_files)
    )

with col2:

    st.metric(
        "Chat Conversations",
        len(st.session_state.chat_history)
    )


st.divider()


# 15. Display selected PDF page preview
if "page_preview" in st.session_state:

    preview = st.session_state["page_preview"]

    st.subheader("📖 PDF Page Preview")

    st.write(f"**Document:** {preview['document']}")

    st.write(f"**Page:** {preview['page']}")

    st.text_area(
        "Extracted page text",
        value=preview["text"],
        height=250,
        disabled=True
    )

    st.divider()


# 16. Chat interface
st.subheader("💬 Ask Your Documents")

st.caption(
    "Ask questions based on your uploaded PDF documents."
)


# 17. Display previous conversations
for chat in st.session_state.chat_history:

    with st.chat_message("user"):

        st.write(chat["question"])

    with st.chat_message("assistant"):

        st.markdown(chat["answer"])

        sources = chat.get("sources", [])

        if sources:

            with st.expander(
                f"📚 View Sources ({len(sources)})"
            ):

                for source in sources:

                    st.markdown(
                        f"**Source {source['source_id']}**"
                    )

                    st.write(
                        f"📄 Document: {source['document']}"
                    )

                    st.write(
                        f"📃 Page: {source['page']}"
                    )

                    with st.expander("View retrieved text"):

                        st.write(source["content"])

                    st.divider()


# 18. Receive user question
question = st.chat_input(
    "Type your question here..."
)


# 19. Generate AI answer
if question:

    if not os.path.exists(
        os.path.join(VECTOR_FOLDER, "index.faiss")
    ):

        st.warning(
            "Please upload and process PDF documents first."
        )

    else:

        try:

            with st.spinner(
                "Searching documents and generating answer..."
            ):

                vector_database = load_vector_database()

                result = ask_question(
                    vector_database,
                    question,
                    st.session_state.chat_history
                )

            new_chat = {
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"]
            }

            st.session_state.chat_history.append(
                new_chat
            )

            save_chat_history(
                st.session_state.chat_history
            )

            st.rerun()

        except Exception as error:

            st.error(
                f"Something went wrong: {error}"
            )


# 20. Welcome message
if not st.session_state.chat_history:

    st.info(
        "👋 Welcome! Upload your PDFs and ask your first question."
    )
