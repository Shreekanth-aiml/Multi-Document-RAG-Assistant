from pypdf import PdfWriter

writer = PdfWriter()

# Create a blank PDF page
writer.add_blank_page(width=300, height=300)

# Protect the PDF with a password
writer.encrypt("12345")

# Save the PDF inside the data folder
with open("data/password_protected.pdf", "wb") as file:
    writer.write(file)

print("Password-protected PDF created successfully!")