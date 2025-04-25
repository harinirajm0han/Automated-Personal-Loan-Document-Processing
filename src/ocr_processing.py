
import os
import re
import streamlit as st
from PIL import Image
import pytesseract
import cv2
import numpy as np
import pandas as pd
from io import BytesIO
import fitz  # PyMuPDF
import tempfile

# Set Tesseract path (update this based on your installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Preprocessing functions
def preprocess_image(image):
    """Enhance image for better OCR results"""
    # Convert to grayscale
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding with Otsu's method
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Remove noise
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    
    return denoised

def extract_text_from_image(image):
    """Extract text from image using OCR"""
    preprocessed = preprocess_image(image)
    text = pytesseract.image_to_string(preprocessed)
    return text

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

# Field extraction functions
def extract_fields(text):
    """Extract key fields from OCR text"""
    fields = {
        'applicant_name': extract_name(text),
        'address': extract_address(text),
        'phone_number': extract_phone(text),
        'email': extract_email(text),
        'income': extract_income(text),
        'loan_amount': extract_loan_amount(text),
        'employment_status': extract_employment_status(text)
    }
    return fields

def extract_name(text):
    """Extract applicant name using regex"""
    name_patterns = [
        r"Name[:,\s]\s*([A-Za-z\s]+)\n",
        r"Applicant[\s\S]*?Name[:,\s]\s*([A-Za-z\s]+)\n",
        r"Full Name[:,\s]\s*([A-Za-z\s]+)\n"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Not found"

def extract_address(text):
    """Extract address using regex"""
    address_pattern = r"(?:Address|Residence)[:,\s]\s*([\w\s,\-\.]+(?:\n[\w\s,\-\.]+)+)"
    match = re.search(address_pattern, text, re.IGNORECASE)
    return match.group(1).replace('\n', ' ').strip() if match else "Not found"

def extract_phone(text):
    """Extract phone number"""
    phone_pattern = r"(?:Phone|Contact|Mobile)[:,\s]\s*([+\d\s\-\(\)]{7,15})"
    match = re.search(phone_pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else "Not found"

# Refined extraction patterns

def extract_email(text):
    """Extract email address"""
    email_pattern = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
    match = re.search(email_pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else "Not found"

# Updated Income extraction with better handling of special characters
def extract_income(text):
    """Extract income information with special characters like $ and §"""
    income_pattern = r"(?:Income|Salary|Annual Salary)[:\s]*([$\d,\.§]+(?:\s?[\w]+)*)"
    match = re.search(income_pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else "Not found"

def extract_job_title(text):
    """Extract job title from the Employment section."""
    job_pattern = r"-Job[:\s]*([A-Za-z\s]+)"
    match = re.search(job_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Not found"

# Determine employment status based on job title
def extract_employment_status(text):
    # If explicitly stated as unemployed
    if re.search(r"\bUnemployed\b", text, re.IGNORECASE):
        return "Unemployed"

    # If job or company is mentioned, assume employed
    if re.search(r"(Job|Position|Company)[:\-]", text, re.IGNORECASE):
        return "Employed"

    # Default to unemployed if no indicators found
    return "Unemployed"


# Extract the loan amount with correct handling of special characters and symbols
def extract_loan_amount(text):
    """Extract loan amount from text extracted from PDF or image."""
    loan_pattern = r"(?:Loan\s*Request|Amount)[^\d\$]{0,10}([\$]?\d[\d,\.]*)"
    match = re.search(loan_pattern, text, re.IGNORECASE)
    if match:
        loan_amount = match.group(1).strip()
        loan_amount = loan_amount.replace(',', '').replace('$', '')
        return loan_amount
    return "Not found"




# Validation functions
def validate_fields(fields):
    """Validate extracted fields"""
    validation_results = {}
    
    # Name validation
    validation_results['applicant_name'] = len(fields['applicant_name'].split()) >= 2 if fields['applicant_name'] != "Not found" else False
    
    # Address validation
    validation_results['address'] = len(fields['address'].split()) >= 3 if fields['address'] != "Not found" else False
    
    # Phone validation
    phone = fields['phone_number']
    validation_results['phone_number'] = re.match(r'^[\d\s+\-\(\)]{7,15}$', phone) is not None if phone != "Not found" else False
    
    # Email validation
    email = fields['email']
    validation_results['email'] = re.match(r'^[^@]+@[^@]+\.[^@]+$', email) is not None if email != "Not found" else False
    
    # Income validation
    income = fields['income']
    validation_results['income'] = re.match(r'^[$\d,\s\.]+$', income) is not None if income != "Not found" else False
    
    # Loan amount validation
    loan_amount = fields['loan_amount']
    validation_results['loan_amount'] = re.match(r'^[$\d,\s\.]+$', loan_amount) is not None if loan_amount != "Not found" else False

    employment_status = fields.get('employment_status', 'Not found')
    validation_results['employment_status'] = employment_status == "Employed"
    
    return validation_results

# Combine extraction and validation
def extract_fields_and_validate(text):
    fields = extract_fields(text)
    validation = validate_fields(fields)

    # Ensure all keys are present in the validation results, even if not found
    validation_results = {
        field: validation.get(field, False) for field in fields.keys()
    }
    
    return fields, validation_results

# Streamlit UI
def main():
    st.title("Personal Loan Application Processor")
    st.markdown("Upload scanned loan application documents to automatically extract key information.")
    
    uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        # Display file info
        file_details = {"Filename": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        st.write(file_details)
        
        # Process file based on type
        if uploaded_file.type == 'application/pdf':
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            # Extract text from PDF
            text = extract_text_from_pdf(tmp_path)
            os.unlink(tmp_path)
            
        else:  # Image file
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Document', use_column_width=True)
            
            # Extract text from image
            text = extract_text_from_image(image)
        
        # Show raw extracted text
        with st.expander("View Extracted Text"):
            st.text(text)
        
        # Extract fields and validation
        if st.button("Extract Information"):
            fields, validation = extract_fields_and_validate(text)
            
            # Display results in a table
            st.subheader("Extracted Information")
            df = pd.DataFrame({
                'Field': fields.keys(),
                'Value': fields.values(),
                'Valid': list(validation.values())
            })
            st.dataframe(df)
            
            # Allow manual correction
            st.subheader("Manual Correction")
            corrected_fields = {}
            for field, value in fields.items():
                corrected_fields[field] = st.text_input(field.replace('_', ' ').title(), value)
            
            if st.button("Save Corrections"):
                st.success("Corrections saved!")
                
                # Here you would typically integrate with your loan processing system
                # For demo purposes, we'll just show the corrected data
                st.subheader("Final Data for System Integration")
                st.json(corrected_fields)
                
                # Simulate integration with bank system
                st.markdown("""
                **Integration Simulation:**
                - Data validated successfully
                - Formatting complete
                - Ready for transfer to loan processing system
                """)

if __name__ == "__main__":
    main()
