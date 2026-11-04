
from PIL import Image, ImageDraw

# Create an image with white background
image = Image.new("RGB", (600, 800), "white")

# Add text to the image
draw = ImageDraw.Draw(image)
draw.text((50, 100), "This is a scanned PDF test.", fill="black")

# Save the image as a PDF
image.save("data/scanned_test.pdf", "PDF")

print("Scanned-style PDF created successfully!")
