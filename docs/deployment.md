# Deployment Guide for Resume Analyzer

## Deployment Options

### 1. Local Deployment
For testing and development:

```bash
# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run Flask application
python app.py
```

### 2. Cloud Platform Deployment

#### Heroku Deployment
1. Create a Heroku account and install Heroku CLI
2. Create a `Procfile` with:
   ```
   web: gunicorn app:app
   ```
3. Add `gunicorn` to `requirements.txt`
4. Deploy using:
   ```bash
   heroku login
   heroku create resume-analyzer
   git push heroku main
   ```

#### Railway/Render Deployment
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
3. Set start command: `gunicorn app:app`

### 3. Docker Deployment

1. Create a `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

2. Build and run:
```bash
docker build -t resume-analyzer .
docker run -p 5000:5000 resume-analyzer
```

## Environment Variables
Set these environment variables for production:
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key`

## Production Considerations

1. **Security**:
   - Use HTTPS
   - Set secure headers
   - Implement rate limiting
   - Configure CORS properly

2. **Storage**:
   - Use cloud storage (AWS S3, Google Cloud Storage) for uploaded files
   - Implement proper file cleanup

3. **Performance**:
   - Enable caching
   - Optimize static assets
   - Configure proper worker processes

4. **Monitoring**:
   - Set up logging
   - Implement error tracking
   - Monitor system resources

5. **Backup**:
   - Regular database backups
   - File storage backups

## Maintenance

1. Regular updates:
   ```bash
   pip install --upgrade -r requirements.txt
   python -m spacy download --upgrade en_core_web_sm
   ```

2. Monitor logs for errors
3. Keep dependencies updated
4. Regular security audits