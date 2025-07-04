import os
import re
import json
import spacy
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline

# For PDF parsing
import pdfplumber

# For DOCX parsing
from docx import Document

class ResumeAnalyzer:
    def __init__(self, resume_path, job_description=''):
        self.resume_path = resume_path
        self.job_description = job_description
        self.resume_text = ''
        self.file_extension = os.path.splitext(resume_path)[1].lower()
        
        # Load NLP model
        try:
            self.nlp = spacy.load('en_core_web_md')
        except OSError:
            # If model not found, download it
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"])
            self.nlp = spacy.load('en_core_web_md')
        
        # Initialize sentiment analyzer for content quality assessment
        self.sentiment_analyzer = pipeline('sentiment-analysis')
        
        # Extract text from resume
        self.extract_text()
        
        # Parse resume sections
        self.parsed_resume = self.parse_resume()
        
    def extract_text(self):
        """Extract text from resume file based on file type"""
        if self.file_extension == '.pdf':
            self.extract_text_from_pdf()
        elif self.file_extension == '.docx':
            self.extract_text_from_docx()
        else:
            raise ValueError(f"Unsupported file format: {self.file_extension}")
    
    def extract_text_from_pdf(self):
        """Extract text from PDF file"""
        text = ""
        with pdfplumber.open(self.resume_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        self.resume_text = text
    
    def extract_text_from_docx(self):
        """Extract text from DOCX file"""
        doc = Document(self.resume_path)
        text = [paragraph.text for paragraph in doc.paragraphs]
        self.resume_text = '\n'.join(text)
    
    def parse_resume(self):
        """Parse resume into sections"""
        # Basic section detection using regex patterns
        sections = {
            'contact_info': self.extract_contact_info(),
            'summary': self.extract_section('summary|profile|objective'),
            'experience': self.extract_section('experience|work|employment|history'),
            'education': self.extract_section('education|academic|qualification'),
            'skills': self.extract_section('skills|expertise|competencies|technologies'),
            'projects': self.extract_section('projects|portfolio'),
            'certifications': self.extract_section('certifications|certificates'),
            'languages': self.extract_section('languages'),
            'interests': self.extract_section('interests|hobbies')
        }
        return sections
    
    def extract_contact_info(self):
        """Extract contact information from resume"""
        # Extract email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = re.findall(email_pattern, self.resume_text)
        email = email_matches[0] if email_matches else ''
        
        # Extract phone number
        phone_pattern = r'(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}'
        phone_matches = re.findall(phone_pattern, self.resume_text)
        phone = phone_matches[0] if phone_matches else ''
        
        # Extract LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_matches = re.findall(linkedin_pattern, self.resume_text, re.IGNORECASE)
        linkedin = linkedin_matches[0] if linkedin_matches else ''
        
        return {
            'email': email,
            'phone': phone,
            'linkedin': linkedin
        }
    
    def extract_section(self, section_pattern):
        """Extract a specific section from the resume text"""
        # Split text into lines for more accurate section detection
        lines = self.resume_text.split('\n')
        
        section_text = []
        in_section = False
        section_header_found = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
                
            # Check if this line starts a new section
            if re.search(f"^\s*({section_pattern})\s*[:\-]?", line, re.IGNORECASE):
                in_section = True
                section_header_found = True
                continue
            
            # Check if we've moved to a different section
            # Look for common section headers that would indicate the end of current section
            next_section_pattern = r"^\s*(EDUCATION|EXPERIENCE|WORK|PROJECTS|CERTIFICATIONS|SUMMARY|OBJECTIVE|CONTACT)\s*[:\-]?"
            if in_section and re.search(next_section_pattern, line, re.IGNORECASE):
                in_section = False
            
            # Special handling for skills section
            if section_pattern.lower().find('skills') >= 0:
                # If we're in the skills section, look for bullet points, commas, or plain text
                if in_section:
                    # Remove bullet points and other common list markers
                    cleaned_line = re.sub(r'^[•\-\*\+]\s*', '', line)
                    # Split by commas if present
                    if ',' in cleaned_line:
                        skills = [skill.strip() for skill in cleaned_line.split(',')]
                        section_text.extend(skills)
                    else:
                        section_text.append(cleaned_line)
            else:
                if in_section:
                    section_text.append(line)
        
        # If no explicit skills section was found, try to extract skills from the entire text
        if section_pattern.lower().find('skills') >= 0 and not section_header_found:
            # Look for skill-like patterns throughout the text
            skill_patterns = [
                r'\b(?:proficient|experienced|skilled|expertise)\s+in\s+([^.]+)',
                r'\b(?:knowledge|understanding)\s+of\s+([^.]+)',
                r'\b(?:technologies|tools|frameworks|languages)\s*:\s*([^.]+)'
            ]
            
            for pattern in skill_patterns:
                matches = re.finditer(pattern, self.resume_text, re.IGNORECASE)
                for match in matches:
                    skills_text = match.group(1)
                    # Split by commas if present
                    if ',' in skills_text:
                        skills = [skill.strip() for skill in skills_text.split(',')]
                        section_text.extend(skills)
                    else:
                        section_text.append(skills_text.strip())
        
        # Clean and deduplicate skills
        if section_pattern.lower().find('skills') >= 0:
            # Remove duplicates while preserving order
            seen = set()
            unique_skills = []
            for skill in section_text:
                skill = skill.strip()
                if skill.lower() not in seen and len(skill) > 1:  # Ignore single characters
                    seen.add(skill.lower())
                    unique_skills.append(skill)
            return '\n'.join(unique_skills)
        
        return '\n'.join(section_text)
    
    def analyze(self):
        """Analyze the resume and return results"""
        # Calculate ATS score
        ats_score = self.calculate_ats_score()
        
        # Generate suggestions
        suggestions = self.generate_suggestions()
        
        # Prepare the analysis result
        analysis_result = {
            'ats_score': ats_score,
            'suggestions': suggestions,
            'parsed_resume': self.parsed_resume
        }
        
        return analysis_result
    
    def calculate_ats_score(self):
        """Calculate ATS score based on various factors"""
        scores = {
            'content': self.evaluate_content(),
            'format': self.evaluate_format(),
            'skills': self.evaluate_skills(),
            'sections': self.evaluate_sections(),
            'style': self.evaluate_style()
        }
        
        # Calculate overall score (weighted average)
        weights = {
            'content': 0.35,
            'format': 0.15,
            'skills': 0.25,
            'sections': 0.15,
            'style': 0.10
        }
        
        overall_score = sum(scores[category] * weights[category] for category in scores)
        
        return {
            'overall': round(overall_score, 1),
            'categories': scores
        }
    
    def evaluate_content(self):
        """Evaluate resume content quality"""
        # Check ATS parse rate
        parse_rate = 1.0 if len(self.resume_text) > 0 else 0.0
        
        # Check for word repetition
        words = re.findall(r'\b\w+\b', self.resume_text.lower())
        word_counts = Counter(words)
        repetition_score = 1.0
        for word, count in word_counts.items():
            if len(word) > 3 and count > 5:  # Only consider words with length > 3 and appearing more than 5 times
                repetition_score -= 0.05  # Penalize for repetition
        repetition_score = max(0.0, repetition_score)  # Ensure score doesn't go below 0
        
        # Check for quantified achievements
        achievement_patterns = [r'\d+%', r'increased', r'decreased', r'improved', r'reduced', r'achieved', r'won', r'awarded']
        achievement_score = 0.0
        for pattern in achievement_patterns:
            if re.search(pattern, self.resume_text, re.IGNORECASE):
                achievement_score += 0.125  # Each pattern adds to the score
        achievement_score = min(1.0, achievement_score)  # Cap at 1.0
        
        # Calculate content score (weighted average)
        content_score = 0.5 * parse_rate + 0.25 * repetition_score + 0.25 * achievement_score
        return round(content_score * 100, 1)
    
    def evaluate_format(self):
        """Evaluate resume format"""
        # Check file format (already validated during upload)
        format_score = 1.0
        
        # Check resume length
        word_count = len(re.findall(r'\b\w+\b', self.resume_text))
        if word_count < 200:
            format_score -= 0.3  # Too short
        elif word_count > 1000:
            format_score -= 0.2  # Too long
        
        # Check for long bullet points
        bullet_points = re.findall(r'[•\-\*]\s*[^•\-\*\n]+', self.resume_text)
        long_bullets = sum(1 for bp in bullet_points if len(bp) > 100)
        if long_bullets > 0:
            format_score -= 0.1 * min(long_bullets, 5)  # Penalize for long bullets, up to 0.5
        
        format_score = max(0.0, format_score)  # Ensure score doesn't go below 0
        return round(format_score * 100, 1)
    
    def evaluate_skills(self):
        """Evaluate skills section"""
        skills_score = 0.0
        
        # Get skills from the parsed resume
        skills_text = self.parsed_resume['skills']
        
        # Initialize skill lists
        hard_skills = {
            'Programming Languages': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'go'],
            'Web Technologies': ['html', 'css', 'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring'],
            'Databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'elasticsearch'],
            'Cloud & DevOps': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'terraform'],
            'Data & Analytics': ['analytics', 'statistics', 'machine learning', 'data science', 'big data', 'tableau', 'power bi'],
            'Business Tools': ['excel', 'powerpoint', 'word', 'jira', 'confluence', 'salesforce', 'sap']
        }
        
        soft_skills = {
            'Communication': ['communication', 'presentation', 'public speaking', 'writing', 'negotiation'],
            'Leadership': ['leadership', 'management', 'team lead', 'mentoring', 'coaching'],
            'Problem Solving': ['problem solving', 'analytical', 'critical thinking', 'troubleshooting', 'decision making'],
            'Teamwork': ['teamwork', 'collaboration', 'team player', 'interpersonal', 'relationship building'],
            'Personal Traits': ['adaptability', 'flexibility', 'creativity', 'initiative', 'attention to detail']
        }
        
        if skills_text:
            # Convert skills text to list if it's not already
            skills = [skill.strip().lower() for skill in skills_text.split('\n') if skill.strip()]
            
            # Calculate hard skills score
            hard_skills_score = 0.0
            hard_skills_found = set()
            for category, category_skills in hard_skills.items():
                category_matches = sum(1 for skill in skills if 
                                     any(hs in skill for hs in category_skills) or 
                                     any(skill in hs for hs in category_skills))
                if category_matches > 0:
                    hard_skills_found.update([skill for skill in skills if 
                                            any(hs in skill for hs in category_skills) or 
                                            any(skill in hs for hs in category_skills)])
                    hard_skills_score += min(1.0, category_matches / 2)  # Aim for at least 2 skills per category
            
            # Normalize hard skills score
            hard_skills_score = min(1.0, hard_skills_score / len(hard_skills))
            
            # Calculate soft skills score
            soft_skills_score = 0.0
            soft_skills_found = set()
            for category, category_skills in soft_skills.items():
                category_matches = sum(1 for skill in skills if 
                                     any(ss in skill for ss in category_skills) or 
                                     any(skill in ss for ss in category_skills))
                if category_matches > 0:
                    soft_skills_found.update([skill for skill in skills if 
                                            any(ss in skill for ss in category_skills) or 
                                            any(skill in ss for ss in category_skills)])
                    soft_skills_score += min(1.0, category_matches / 2)  # Aim for at least 2 skills per category
            
            # Normalize soft skills score
            soft_skills_score = min(1.0, soft_skills_score / len(soft_skills))
            
            # Calculate initial skills score with more weight on hard skills
            skills_score = 0.7 * hard_skills_score + 0.3 * soft_skills_score
            
            # Bonus points for having a good balance of skills
            if len(hard_skills_found) >= 5 and len(soft_skills_found) >= 3:
                skills_score = min(1.0, skills_score + 0.1)  # Bonus for good balance
        
        # If job description is provided, check for keyword matching
        if self.job_description:
            # Extract potential skills from job description
            job_skills = set()
            for skill_lists in hard_skills.values():
                job_skills.update(skill for skill in skill_lists 
                                if any(skill.lower() in self.job_description.lower() for skill in skill_lists))
            for skill_lists in soft_skills.values():
                job_skills.update(skill for skill in skill_lists 
                                if any(skill.lower() in self.job_description.lower() for skill in skill_lists))
            
            if job_skills:
                # Calculate match ratio based on found skills
                skills_lower = [skill.lower() for skill in skills]
                match_count = sum(1 for job_skill in job_skills 
                                if any(job_skill in skill for skill in skills_lower))
                match_ratio = min(1.0, match_count / len(job_skills))
                
                # Adjust skills score based on keyword matching
                skills_score = 0.6 * skills_score + 0.4 * match_ratio
        
        return round(skills_score * 100, 1)
    
    def evaluate_sections(self):
        """Evaluate resume sections"""
        sections_score = 0.0
        
        # Check for essential sections
        essential_sections = ['contact_info', 'experience', 'education', 'skills']
        essential_score = sum(1 for section in essential_sections if self.parsed_resume[section]) / len(essential_sections)
        
        # Check contact information completeness
        contact_info = self.parsed_resume['contact_info']
        contact_score = sum(1 for field in contact_info if contact_info[field]) / len(contact_info)
        
        # Check for personality showcase (additional sections)
        additional_sections = ['summary', 'projects', 'certifications', 'languages', 'interests']
        additional_score = min(1.0, sum(1 for section in additional_sections if self.parsed_resume[section]) / 3)  # Aim for at least 3 additional sections
        
        # Calculate sections score (weighted average)
        sections_score = 0.5 * essential_score + 0.3 * contact_score + 0.2 * additional_score
        return round(sections_score * 100, 1)
    
    def evaluate_style(self):
        """Evaluate resume style"""
        style_score = 0.5  # Start with a base score
        
        # Check email address format
        email = self.parsed_resume['contact_info']['email']
        if email and ('@gmail.com' in email or '@yahoo.com' in email or '@hotmail.com' in email):
            style_score += 0.1  # Professional email
        
        # Check for active voice
        active_voice_patterns = [r'\b(managed|developed|created|implemented|led|achieved|increased|decreased|improved|reduced)\b']
        active_voice_count = sum(len(re.findall(pattern, self.resume_text, re.IGNORECASE)) for pattern in active_voice_patterns)
        if active_voice_count > 5:
            style_score += 0.2  # Good use of active voice
        
        # Check for buzzwords and cliches
        buzzwords = ['synergy', 'think outside the box', 'go-getter', 'team player', 'detail-oriented', 'proactive', 
                    'go-to person', 'results-driven', 'hardworking', 'multitasker', 'self-motivated', 'dynamic']
        buzzword_count = sum(self.resume_text.lower().count(word) for word in buzzwords)
        if buzzword_count > 3:
            style_score -= 0.2  # Penalize for buzzword overuse
        
        style_score = max(0.0, min(1.0, style_score))  # Ensure score is between 0 and 1
        return round(style_score * 100, 1)
    
    def generate_suggestions(self):
        """Generate suggestions for improving the resume"""
        suggestions = {
            'content': [],
            'format': [],
            'skills': [],
            'sections': [],
            'style': []
        }
        
        # Content suggestions
        if self.evaluate_content() < 70:
            # Check for word repetition
            words = re.findall(r'\b\w+\b', self.resume_text.lower())
            word_counts = Counter(words)
            repeated_words = [word for word, count in word_counts.items() if len(word) > 3 and count > 5]
            if repeated_words:
                suggestions['content'].append(f"Consider using synonyms for frequently repeated words: {', '.join(repeated_words[:5])}.")
            
            # Check for quantified achievements
            if not any(re.search(pattern, self.resume_text, re.IGNORECASE) for pattern in [r'\d+%', r'increased', r'decreased']):
                suggestions['content'].append("Add quantifiable achievements to your experience section (e.g., 'Increased sales by 20%').")
        
        # Format suggestions
        if self.evaluate_format() < 70:
            word_count = len(re.findall(r'\b\w+\b', self.resume_text))
            if word_count < 200:
                suggestions['format'].append("Your resume is too short. Consider adding more details about your experience and skills.")
            elif word_count > 1000:
                suggestions['format'].append("Your resume is too long. Try to keep it concise and focused on the most relevant information.")
            
            # Check for long bullet points
            bullet_points = re.findall(r'[•\-\*]\s*[^•\-\*\n]+', self.resume_text)
            long_bullets = [bp for bp in bullet_points if len(bp) > 100]
            if long_bullets:
                suggestions['format'].append("Some bullet points are too long. Keep them concise and focused on one achievement or responsibility.")
        
        # Skills suggestions
        if self.evaluate_skills() < 70:
            # Suggest hard skills based on job description or common skills
            hard_skills = ['Python', 'Java', 'JavaScript', 'HTML', 'CSS', 'SQL', 'React', 'Angular', 'Node.js', 'AWS', 'Azure', 
                          'Excel', 'PowerPoint', 'Word', 'Photoshop', 'Illustrator', 'Analytics', 'Statistics', 'Research', 
                          'Marketing', 'Sales', 'Finance', 'Accounting', 'Management', 'Leadership', 'Project Management']
            
            # Filter skills not mentioned in resume
            missing_hard_skills = [skill for skill in hard_skills if skill.lower() not in self.resume_text.lower()]
            if missing_hard_skills and len(missing_hard_skills) > 20:
                suggestions['skills'].append(f"Consider adding relevant hard skills such as: {', '.join(missing_hard_skills[:5])}.")
            
            # Suggest soft skills
            soft_skills = ['Communication', 'Teamwork', 'Problem Solving', 'Creativity', 'Adaptability', 'Leadership', 
                          'Time Management', 'Critical Thinking', 'Decision Making', 'Organization']
            missing_soft_skills = [skill for skill in soft_skills if skill.lower() not in self.resume_text.lower()]
            if missing_soft_skills and len(missing_soft_skills) > 5:
                suggestions['skills'].append(f"Consider adding relevant soft skills such as: {', '.join(missing_soft_skills[:3])}.")
            
            # Keyword matching with job description
            if self.job_description:
                job_keywords = set(re.findall(r'\b[A-Za-z][A-Za-z\s]*[A-Za-z]\b', self.job_description.lower()))
                resume_keywords = set(re.findall(r'\b[A-Za-z][A-Za-z\s]*[A-Za-z]\b', self.resume_text.lower()))
                
                # Find important keywords in job description not in resume
                missing_keywords = job_keywords - resume_keywords
                if missing_keywords:
                    suggestions['skills'].append(f"Consider adding these keywords from the job description: {', '.join(list(missing_keywords)[:5])}.")
        
        # Sections suggestions
        if self.evaluate_sections() < 70:
            # Check for essential sections
            essential_sections = {'contact_info': 'Contact Information', 'experience': 'Work Experience', 'education': 'Education', 'skills': 'Skills'}
            missing_sections = [essential_sections[section] for section in essential_sections if not self.parsed_resume[section]]
            if missing_sections:
                suggestions['sections'].append(f"Add these essential sections to your resume: {', '.join(missing_sections)}.")
            
            # Check contact information completeness
            contact_info = self.parsed_resume['contact_info']
            missing_contact = [field for field in contact_info if not contact_info[field]]
            if missing_contact:
                contact_fields = {'email': 'Email', 'phone': 'Phone Number', 'linkedin': 'LinkedIn Profile'}
                suggestions['sections'].append(f"Add these contact details: {', '.join([contact_fields[field] for field in missing_contact])}.")
            
            # Suggest additional sections
            additional_sections = {'summary': 'Professional Summary', 'projects': 'Projects', 'certifications': 'Certifications', 
                                 'languages': 'Languages', 'interests': 'Interests/Hobbies'}
            missing_additional = [additional_sections[section] for section in additional_sections if not self.parsed_resume[section]]
            if len(missing_additional) > 2:  # If missing more than 2 additional sections
                suggestions['sections'].append(f"Consider adding these sections to showcase your personality: {', '.join(missing_additional[:2])}.")
        
        # Style suggestions
        if self.evaluate_style() < 70:
            # Check email address format
            email = self.parsed_resume['contact_info']['email']
            if email and not ('@gmail.com' in email or '@yahoo.com' in email or '@hotmail.com' in email or '@outlook.com' in email):
                suggestions['style'].append("Consider using a professional email address.")
            
            # Check for active voice
            active_voice_patterns = [r'\b(managed|developed|created|implemented|led|achieved|increased|decreased|improved|reduced)\b']
            active_voice_count = sum(len(re.findall(pattern, self.resume_text, re.IGNORECASE)) for pattern in active_voice_patterns)
            if active_voice_count < 5:
                suggestions['style'].append("Use more active voice verbs to describe your achievements and responsibilities.")
            
            # Check for buzzwords and cliches
            buzzwords = ['synergy', 'think outside the box', 'go-getter', 'team player', 'detail-oriented', 'proactive', 
                        'go-to person', 'results-driven', 'hardworking', 'multitasker', 'self-motivated', 'dynamic']
            buzzword_count = sum(self.resume_text.lower().count(word) for word in buzzwords)
            if buzzword_count > 3:
                suggestions['style'].append("Reduce the use of buzzwords and cliches. Be more specific about your skills and achievements.")
        
        return suggestions