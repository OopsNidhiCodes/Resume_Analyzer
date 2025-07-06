# Resume Analyzer

Resume Analyzer is a web application that analyzes resumes (PDF/DOCX) for ATS (Applicant Tracking System) compatibility, section completeness, skill coverage, and formatting. It provides actionable suggestions and generates downloadable PDF reports.

## Features
- Upload resumes in PDF or DOCX format
- Extracts and parses resume sections (Contact Info, Skills, Experience, Education, etc.)
- Calculates ATS score and category-wise breakdown (content, format, skills, sections, style)
- Provides suggestions for improvement
- Supports job description matching for skill relevance
- Downloadable PDF and JSON analysis reports

## Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Resume_Analyzer.git
   cd Resume_Analyzer
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   - Make sure you have Python 3.8+ installed.
   - The app uses `spacy` and `transformers` for NLP, `pdfplumber` for PDF parsing, and `xhtml2pdf` for PDF report generation.
3. **Download spaCy model:**
   ```bash
   python -m spacy download en_core_web_md
   ```

## Local Development
1. **Start the Flask server:**
   ```bash
   python -m flask run
   ```
2. **Open your browser and go to:**
   [http://localhost:5000/](http://localhost:5000/)
3. **Upload a resume and (optionally) a job description.**
4. **View analysis results and download the PDF report.**

## Deployment Options

### 1. Docker Deployment (Recommended)
1. **Using Docker Compose (Easiest):**
   ```bash
   docker-compose up -d
   ```
   This will build and start the application with all necessary configurations.

2. **Using Docker directly:**
   ```bash
   docker build -t resume-analyzer .
   docker run -p 5000:5000 resume-analyzer
   ```

### 2. Cloud Platform Deployment

Detailed deployment guides for various platforms are available in the `docs/deployment.md` file, including:
- Heroku deployment
- Railway/Render deployment
- Production considerations
- Environment configuration
- Maintenance guidelines

## Project Structure
```
Resume_Analyzer/
├── analyzer/
│   └── resume_analyzer.py      # Resume analysis logic
├── app.py                     # Flask web server
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
├── docs/
│   └── deployment.md          # Deployment documentation
├── results/                   # Stores analysis result JSON files
├── static/
│   ├── css/style.css          # Styles
│   └── js/script.js           # Frontend logic
├── templates/
│   └── index.html             # Main HTML page
├── uploads/                   # Uploaded resumes
```

## Production Considerations
- Set appropriate environment variables (FLASK_ENV, SECRET_KEY)
- Configure HTTPS and secure headers
- Implement proper file storage solution
- Set up monitoring and logging
- Regular backups and maintenance

## Notes
- For image-based PDFs, text extraction may be limited. Consider using OCR tools for better results.
- The skills section detection and scoring logic is customizable in `analyzer/resume_analyzer.py`.
- Reports are saved in the `results/` folder and can be downloaded as PDF or JSON.

## License
MIT License