import os
from faker import Faker
from PIL import Image, ImageDraw, ImageFont
import random
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import cv2

# Ensure the directories exist
os.makedirs(r"C:\Users\Harini Rajmohan\OneDrive\Desktop\TCS Hackathon\data\images", exist_ok=True)
os.makedirs(r"C:\Users\Harini Rajmohan\OneDrive\Desktop\TCS Hackathon\data\pdfs", exist_ok=True)

fake = Faker()

def generate_loan_application():
    name = fake.name()
    address = fake.address().replace("\n", ", ")
    income = f"${random.randint(30_000, 150_000):,}"
    loan_amount = f"${random.randint(5_000, 50_000):,}"
    
    return f"""
    PERSONAL LOAN APPLICATION
    --------------------------
    Name: {name}
    Address: {address}
    Phone: {fake.phone_number()}
    Email: {fake.email()}
    
    Employment:
    - Company: {fake.company()}
    - Job: {fake.job()}
    - Income: {income}
    
    Loan Request:
    - Amount: {loan_amount}
    - Purpose: {random.choice(['Home', 'Car', 'Education', 'Medical'])}
    """

# Set font for PDF generation
font_path = r"C:\Windows\Fonts\Arial.ttf"  # Arial font, easy to read and OCR-friendly
font_size = 12

# Generate 10 samples (PDF + Image)
for i in range(1, 11):
    text = generate_loan_application()
    
    # Save as PDF with better alignment and font
    pdf_path = os.path.join(r"C:\Users\Harini Rajmohan\OneDrive\Desktop\TCS Hackathon\data\pdfs", f"loan_app_{i}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", font_size)  # Use a common legible font (Helvetica)
    
    # Write the title with bold and larger font size
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 750, "PERSONAL LOAN APPLICATION")
    
    c.setFont("Helvetica", font_size)
    y_position = 720
    line_spacing = 15
    
    # Write the content
    for line in text.splitlines():
        c.drawString(50, y_position, line)
        y_position -= line_spacing
        
        if y_position < 50:  # Start a new page if there's no room left
            c.showPage()
            c.setFont("Helvetica", font_size)
            y_position = 750
    
    c.save()
    
    # Save as Image (with better legibility)
    img_path = os.path.join(r"C:\Users\Harini Rajmohan\OneDrive\Desktop\TCS Hackathon\data\images", f"loan_app_{i}.jpg")
    img = Image.new("RGB", (800, 600), "white")
    draw = ImageDraw.Draw(img)
    
    # Set font size and type
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    
    # Draw the text onto the image, ensuring proper spacing and alignment
    y_position = 50
    for line in text.splitlines():
        draw.text((50, y_position), line, fill="black", font=font)
        y_position += line_spacing
    
    img.save(img_path)

    # Display Image in terminal (using OpenCV)
    img_cv = cv2.imread(img_path)
    cv2.imshow(f"Loan Application {i}", img_cv)
    cv2.waitKey(0)  # Wait until a key is pressed
    cv2.destroyAllWindows()

print("✅ Generated 10 sample PDFs + Images in /data/")
