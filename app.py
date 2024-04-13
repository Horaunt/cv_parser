from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import re
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as f:
        reader = PdfReader(f)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text

def extract_info(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b'
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    
    # Pad the shorter array with empty strings to make them equal in length
    max_length = max(len(emails), len(phones))
    emails += [''] * (max_length - len(emails))
    phones += [''] * (max_length - len(phones))
    
    return {'emails': emails, 'phones': phones}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(file_path)
        else:
            return jsonify({'error': 'Unsupported file format'})
        
        info = extract_info(text)
        print("Extracted info:", info)  # Add this line for debugging
        df = pd.DataFrame(info)
        print("DataFrame shape:", df.shape)  # Add this line for debugging
        excel_path = os.path.join('output', 'cv_info.xlsx')
        df.to_excel(excel_path, index=False)
        
        return jsonify({'success': True, 'excel_path': excel_path})
    else:
        return jsonify({'error': 'Unsupported file type'})


if __name__ == '__main__':
    app.run(debug=True)
