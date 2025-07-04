import os
from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import time
from datetime import datetime
import uuid
from xhtml2pdf import pisa
from io import BytesIO
import tempfile

# Import the resume analyzer module
from analyzer.resume_analyzer import ResumeAnalyzer

app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create results folder if it doesn't exist
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['resume']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Please upload PDF or DOCX files only.'}), 400
    
    # Get job description if provided
    job_description = request.form.get('job_description', '')
    
    # Generate a unique filename
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{unique_id}_{filename}"
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)
    
    try:
        # Initialize the resume analyzer
        analyzer = ResumeAnalyzer(file_path, job_description)
        
        # Analyze the resume
        analysis_result = analyzer.analyze()
        
        # Add result_id to the analysis result
        analysis_result['result_id'] = unique_id
        
        # Save the analysis result
        result_filename = f"{timestamp}_{unique_id}_result.json"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        
        with open(result_path, 'w') as f:
            json.dump(analysis_result, f)
        
        return jsonify({
            'success': True,
            'result_id': unique_id,
            'analysis': analysis_result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results/<result_id>')
def get_result(result_id):
    # Find the result file with the given ID
    for filename in os.listdir(RESULTS_FOLDER):
        if result_id in filename and filename.endswith('_result.json'):
            with open(os.path.join(RESULTS_FOLDER, filename), 'r') as f:
                return jsonify(json.load(f))
    
    return jsonify({'error': 'Result not found'}), 404

@app.route('/download-pdf/<result_id>')
def download_pdf_report(result_id):
    # Find the result file with the given ID
    result_data = None
    for filename in os.listdir(RESULTS_FOLDER):
        if result_id in filename and filename.endswith('_result.json'):
            with open(os.path.join(RESULTS_FOLDER, filename), 'r') as f:
                result_data = json.load(f)
                break
    
    if not result_data:
        return jsonify({'error': 'Result not found'}), 404
    
    # Generate PDF report
    pdf_content = generate_pdf_report(result_data)
    
    # Create response with PDF
    response = make_response(pdf_content)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=resume_analysis_report.pdf'
    
    return response

def generate_pdf_report(data):
    # Create HTML content for the PDF
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get scores
    overall_score = data['ats_score']['overall']
    category_scores = data['ats_score']['categories']
    suggestions = data['suggestions']
    
    # Create HTML content
    html = f'''
    <html>
    <head>
        <title>Resume Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .score-overview {{ margin-bottom: 20px; }}
            .score-box {{ 
                display: inline-block; 
                width: 100px; 
                height: 100px; 
                line-height: 100px; 
                text-align: center; 
                font-size: 36px; 
                font-weight: bold; 
                border-radius: 50%; 
                margin: 0 auto; 
                color: white;
            }}
            .good {{ background-color: #28a745; }}
            .average {{ background-color: #ffc107; }}
            .poor {{ background-color: #dc3545; }}
            .category-scores {{ margin-bottom: 30px; }}
            .category {{ margin-bottom: 10px; }}
            .category-name {{ display: inline-block; width: 100px; }}
            .category-score {{ 
                display: inline-block; 
                width: 40px; 
                text-align: center; 
                font-weight: bold; 
                margin-right: 10px; 
            }}
            .progress {{ 
                display: inline-block; 
                width: 300px; 
                height: 20px; 
                background-color: #f0f0f0; 
                border-radius: 10px; 
                overflow: hidden; 
            }}
            .progress-bar {{ 
                height: 100%; 
                border-radius: 10px; 
            }}
            .suggestions {{ margin-bottom: 30px; }}
            .suggestion-category {{ margin-bottom: 20px; }}
            .timestamp {{ text-align: right; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Resume Analysis Report</h1>
            <p>This report provides an analysis of your resume's ATS compatibility and suggestions for improvement.</p>
        </div>
        
        <div class="score-overview">
            <h2>Overall ATS Score</h2>
            <div class="score-box {'good' if overall_score >= 80 else 'average' if overall_score >= 60 else 'poor'}">
                {overall_score}
            </div>
            <p>{'Your resume is well-optimized for ATS systems.' if overall_score >= 80 else 
               'Your resume needs some improvements for better ATS compatibility.' if overall_score >= 60 else 
               'Your resume needs significant improvements for ATS compatibility.'}</p>
        </div>
        
        <div class="category-scores">
            <h2>Category Scores</h2>
            
            <div class="category">
                <span class="category-name">Content:</span>
                <span class="category-score">{category_scores['content']}</span>
                <div class="progress">
                    <div class="progress-bar" style="width: {category_scores['content']}%; 
                         background-color: {'#28a745' if category_scores['content'] >= 80 else '#ffc107' if category_scores['content'] >= 60 else '#dc3545'}"></div>
                </div>
            </div>
            
            <div class="category">
                <span class="category-name">Format:</span>
                <span class="category-score">{category_scores['format']}</span>
                <div class="progress">
                    <div class="progress-bar" style="width: {category_scores['format']}%; 
                         background-color: {'#28a745' if category_scores['format'] >= 80 else '#ffc107' if category_scores['format'] >= 60 else '#dc3545'}"></div>
                </div>
            </div>
            
            <div class="category">
                <span class="category-name">Skills:</span>
                <span class="category-score">{category_scores['skills']}</span>
                <div class="progress">
                    <div class="progress-bar" style="width: {category_scores['skills']}%; 
                         background-color: {'#28a745' if category_scores['skills'] >= 80 else '#ffc107' if category_scores['skills'] >= 60 else '#dc3545'}"></div>
                </div>
            </div>
            
            <div class="category">
                <span class="category-name">Sections:</span>
                <span class="category-score">{category_scores['sections']}</span>
                <div class="progress">
                    <div class="progress-bar" style="width: {category_scores['sections']}%; 
                         background-color: {'#28a745' if category_scores['sections'] >= 80 else '#ffc107' if category_scores['sections'] >= 60 else '#dc3545'}"></div>
                </div>
            </div>
            
            <div class="category">
                <span class="category-name">Style:</span>
                <span class="category-score">{category_scores['style']}</span>
                <div class="progress">
                    <div class="progress-bar" style="width: {category_scores['style']}%; 
                         background-color: {'#28a745' if category_scores['style'] >= 80 else '#ffc107' if category_scores['style'] >= 60 else '#dc3545'}"></div>
                </div>
            </div>
        </div>
        
        <div class="suggestions">
            <h2>Improvement Suggestions</h2>
            
            <div class="suggestion-category">
                <h3>Content Suggestions</h3>
                {'<ul>' + ''.join([f'<li>{suggestion}</li>' for suggestion in suggestions['content']]) + '</ul>' if suggestions['content'] else '<p>Great job! No content improvements needed.</p>'}
            </div>
            
            <div class="suggestion-category">
                <h3>Format Suggestions</h3>
                {'<ul>' + ''.join([f'<li>{suggestion}</li>' for suggestion in suggestions['format']]) + '</ul>' if suggestions['format'] else '<p>Great job! No format improvements needed.</p>'}
            </div>
            
            <div class="suggestion-category">
                <h3>Skills Suggestions</h3>
                {'<ul>' + ''.join([f'<li>{suggestion}</li>' for suggestion in suggestions['skills']]) + '</ul>' if suggestions['skills'] else '<p>Great job! No skills improvements needed.</p>'}
            </div>
            
            <div class="suggestion-category">
                <h3>Sections Suggestions</h3>
                {'<ul>' + ''.join([f'<li>{suggestion}</li>' for suggestion in suggestions['sections']]) + '</ul>' if suggestions['sections'] else '<p>Great job! No section improvements needed.</p>'}
            </div>
            
            <div class="suggestion-category">
                <h3>Style Suggestions</h3>
                {'<ul>' + ''.join([f'<li>{suggestion}</li>' for suggestion in suggestions['style']]) + '</ul>' if suggestions['style'] else '<p>Great job! No style improvements needed.</p>'}
            </div>
        </div>
        
        <div class="timestamp">
            <p>Report generated on: {timestamp}</p>
        </div>
    </body>
    </html>
    '''
    
    # Convert HTML to PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result)
    
    if not pdf.err:
        return result.getvalue()
    else:
        return None

if __name__ == '__main__':
    app.run(debug=True)