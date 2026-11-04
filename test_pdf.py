from document_processor import extract_text_from_pdf, split_text_into_chunks

pdf_path = "data/sample.pdf"

# Extract text from the PDF
text = extract_text_from_pdf(pdf_path)

# Split extracted text into chunks
chunks = split_text_into_chunks(text)

print("PDF Processing Successful!")
print("Total chunks:", len(chunks))

# Display the first chunk
print("\nFirst Chunk:")
print(chunks[0])