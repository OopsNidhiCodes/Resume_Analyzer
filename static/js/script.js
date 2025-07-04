document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const resumeForm = document.getElementById('resume-form');
    const resumeFileInput = document.getElementById('resume-file');
    const browseBtn = document.getElementById('browse-btn');
    const dropArea = document.getElementById('drop-area');
    const selectedFileContainer = document.getElementById('selected-file-container');
    const fileName = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file');
    const analyzeBtn = document.getElementById('analyze-btn');
    const jobDescription = document.getElementById('job-description');
    
    const uploadSection = document.querySelector('.upload-section');
    const loadingSection = document.querySelector('.loading-section');
    const resultsSection = document.querySelector('.results-section');
    
    const scoreCircle = document.getElementById('score-circle');
    const scoreText = document.querySelector('.score-text');
    
    const contentProgress = document.getElementById('content-progress');
    const formatProgress = document.getElementById('format-progress');
    const skillsProgress = document.getElementById('skills-progress');
    const sectionsProgress = document.getElementById('sections-progress');
    const styleProgress = document.getElementById('style-progress');
    
    const contentScore = document.getElementById('content-score');
    const formatScore = document.getElementById('format-score');
    const skillsScore = document.getElementById('skills-score');
    const sectionsScore = document.getElementById('sections-score');
    const styleScore = document.getElementById('style-score');
    
    const contentSuggestions = document.getElementById('content-suggestions').querySelector('ul');
    const formatSuggestions = document.getElementById('format-suggestions').querySelector('ul');
    const skillsSuggestions = document.getElementById('skills-suggestions').querySelector('ul');
    const sectionsSuggestions = document.getElementById('sections-suggestions').querySelector('ul');
    const styleSuggestions = document.getElementById('style-suggestions').querySelector('ul');
    
    const resumeSectionsAccordion = document.getElementById('resume-sections-accordion');
    
    const downloadReportBtn = document.getElementById('download-report');
    const analyzeNewBtn = document.getElementById('analyze-new');
    
    // Current analysis result
    let currentAnalysis = null;
    
    // File Upload Handling
    browseBtn.addEventListener('click', () => {
        resumeFileInput.click();
    });
    
    resumeFileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('dragover');
    }
    
    function unhighlight() {
        dropArea.classList.remove('dragover');
    }
    
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            resumeFileInput.files = files;
            handleFileSelect();
        }
    }
    
    function handleFileSelect() {
        if (resumeFileInput.files.length > 0) {
            const file = resumeFileInput.files[0];
            
            // Check file type
            const fileType = file.name.split('.').pop().toLowerCase();
            if (fileType !== 'pdf' && fileType !== 'docx') {
                alert('Please upload a PDF or DOCX file only.');
                resetFileInput();
                return;
            }
            
            // Check file size (max 2MB)
            if (file.size > 2 * 1024 * 1024) {
                alert('File size exceeds 2MB. Please upload a smaller file.');
                resetFileInput();
                return;
            }
            
            // Display selected file
            fileName.textContent = file.name;
            selectedFileContainer.style.display = 'flex';
            dropArea.style.display = 'none';
            analyzeBtn.disabled = false;
        }
    }
    
    function resetFileInput() {
        resumeFileInput.value = '';
        fileName.textContent = 'No file selected';
        selectedFileContainer.style.display = 'none';
        dropArea.style.display = 'block';
        analyzeBtn.disabled = true;
    }
    
    removeFileBtn.addEventListener('click', resetFileInput);
    
    // Form Submission
    resumeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!resumeFileInput.files.length) {
            alert('Please select a resume file.');
            return;
        }
        
        // Show loading section
        uploadSection.style.display = 'none';
        loadingSection.style.display = 'block';
        resultsSection.style.display = 'none';
        
        // Create form data
        const formData = new FormData();
        formData.append('resume', resumeFileInput.files[0]);
        formData.append('job_description', jobDescription.value);
        
        // Send request to server
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Something went wrong');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading section
            loadingSection.style.display = 'none';
            
            // Store current analysis
            currentAnalysis = data.analysis;
            
            // Display results
            displayResults(data.analysis);
            
            // Show results section
            resultsSection.style.display = 'block';
        })
        .catch(error => {
            alert('Error: ' + error.message);
            // Go back to upload section
            uploadSection.style.display = 'block';
            loadingSection.style.display = 'none';
        });
    });
    
    // Display Results
    function displayResults(analysis) {
        // Display overall score
        const overallScore = analysis.ats_score.overall;
        scoreCircle.setAttribute('stroke-dasharray', `${overallScore}, 100`);
        scoreText.textContent = overallScore;
        
        // Set score color based on value
        if (overallScore >= 80) {
            scoreCircle.style.stroke = '#28a745'; // Green for good score
        } else if (overallScore >= 60) {
            scoreCircle.style.stroke = '#ffc107'; // Yellow for average score
        } else {
            scoreCircle.style.stroke = '#dc3545'; // Red for poor score
        }
        
        // Display category scores
        const categoryScores = analysis.ats_score.categories;
        
        contentScore.textContent = categoryScores.content;
        formatScore.textContent = categoryScores.format;
        skillsScore.textContent = categoryScores.skills;
        sectionsScore.textContent = categoryScores.sections;
        styleScore.textContent = categoryScores.style;
        
        contentProgress.style.width = `${categoryScores.content}%`;
        formatProgress.style.width = `${categoryScores.format}%`;
        skillsProgress.style.width = `${categoryScores.skills}%`;
        sectionsProgress.style.width = `${categoryScores.sections}%`;
        styleProgress.style.width = `${categoryScores.style}%`;
        
        // Set progress bar colors based on scores
        setProgressColor(contentProgress, categoryScores.content);
        setProgressColor(formatProgress, categoryScores.format);
        setProgressColor(skillsProgress, categoryScores.skills);
        setProgressColor(sectionsProgress, categoryScores.sections);
        setProgressColor(styleProgress, categoryScores.style);
        
        // Display suggestions
        displaySuggestions(analysis.suggestions);
        
        // Display parsed resume sections
        displayParsedResume(analysis.parsed_resume);
    }
    
    function setProgressColor(progressElement, score) {
        if (score >= 80) {
            progressElement.style.backgroundColor = '#28a745'; // Green
        } else if (score >= 60) {
            progressElement.style.backgroundColor = '#ffc107'; // Yellow
        } else {
            progressElement.style.backgroundColor = '#dc3545'; // Red
        }
    }
    
    function displaySuggestions(suggestions) {
        // Clear previous suggestions
        contentSuggestions.innerHTML = '';
        formatSuggestions.innerHTML = '';
        skillsSuggestions.innerHTML = '';
        sectionsSuggestions.innerHTML = '';
        styleSuggestions.innerHTML = '';
        
        // Add new suggestions
        if (suggestions.content.length > 0) {
            suggestions.content.forEach(suggestion => {
                const li = document.createElement('li');
                li.textContent = suggestion;
                contentSuggestions.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Great job! No content improvements needed.';
            contentSuggestions.appendChild(li);
        }
        
        if (suggestions.format.length > 0) {
            suggestions.format.forEach(suggestion => {
                const li = document.createElement('li');
                li.textContent = suggestion;
                formatSuggestions.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Great job! No format improvements needed.';
            formatSuggestions.appendChild(li);
        }
        
        if (suggestions.skills.length > 0) {
            suggestions.skills.forEach(suggestion => {
                const li = document.createElement('li');
                li.textContent = suggestion;
                skillsSuggestions.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Great job! No skills improvements needed.';
            skillsSuggestions.appendChild(li);
        }
        
        if (suggestions.sections.length > 0) {
            suggestions.sections.forEach(suggestion => {
                const li = document.createElement('li');
                li.textContent = suggestion;
                sectionsSuggestions.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Great job! No section improvements needed.';
            sectionsSuggestions.appendChild(li);
        }
        
        if (suggestions.style.length > 0) {
            suggestions.style.forEach(suggestion => {
                const li = document.createElement('li');
                li.textContent = suggestion;
                styleSuggestions.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Great job! No style improvements needed.';
            styleSuggestions.appendChild(li);
        }
    }
    
    function displayParsedResume(parsedResume) {
        // Clear previous content
        resumeSectionsAccordion.innerHTML = '';
        
        // Define section icons and titles
        const sectionInfo = {
            'contact_info': { icon: 'fa-address-card', title: 'Contact Information' },
            'summary': { icon: 'fa-file-alt', title: 'Professional Summary' },
            'experience': { icon: 'fa-briefcase', title: 'Work Experience' },
            'education': { icon: 'fa-graduation-cap', title: 'Education' },
            'skills': { icon: 'fa-tools', title: 'Skills' },
            'projects': { icon: 'fa-project-diagram', title: 'Projects' },
            'certifications': { icon: 'fa-certificate', title: 'Certifications' },
            'languages': { icon: 'fa-language', title: 'Languages' },
            'interests': { icon: 'fa-heart', title: 'Interests' }
        };
        
        // Add each section to the accordion
        for (const [section, content] of Object.entries(parsedResume)) {
            // Skip empty sections
            if (section === 'contact_info') {
                if (!content.email && !content.phone && !content.linkedin) {
                    continue;
                }
            } else if (!content || content.trim() === '') {
                continue;
            }
            
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item';
            
            const accordionHeader = document.createElement('div');
            accordionHeader.className = 'accordion-header';
            accordionHeader.dataset.section = section;
            
            const icon = document.createElement('i');
            icon.className = `fas ${sectionInfo[section].icon}`;
            
            const span = document.createElement('span');
            span.textContent = sectionInfo[section].title;
            
            const chevron = document.createElement('i');
            chevron.className = 'fas fa-chevron-down';
            
            accordionHeader.appendChild(icon);
            accordionHeader.appendChild(span);
            accordionHeader.appendChild(chevron);
            
            const accordionContent = document.createElement('div');
            accordionContent.className = 'accordion-content';
            accordionContent.id = `${section}-content`;
            
            // Format content based on section type
            if (section === 'contact_info') {
                const contactList = document.createElement('ul');
                
                if (content.email) {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>Email:</strong> ${content.email}`;
                    contactList.appendChild(li);
                }
                
                if (content.phone) {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>Phone:</strong> ${content.phone}`;
                    contactList.appendChild(li);
                }
                
                if (content.linkedin) {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>LinkedIn:</strong> ${content.linkedin}`;
                    contactList.appendChild(li);
                }
                
                accordionContent.appendChild(contactList);
            } else {
                const p = document.createElement('p');
                p.textContent = content;
                accordionContent.appendChild(p);
            }
            
            accordionItem.appendChild(accordionHeader);
            accordionItem.appendChild(accordionContent);
            
            resumeSectionsAccordion.appendChild(accordionItem);
        }
        
        // Add click event listeners to accordion headers
        const accordionHeaders = document.querySelectorAll('.accordion-header');
        accordionHeaders.forEach(header => {
            header.addEventListener('click', toggleAccordion);
        });
    }
    
    // Accordion functionality
    function toggleAccordion() {
        this.classList.toggle('active');
        const content = this.nextElementSibling;
        content.classList.toggle('active');
    }
    
    // Add click event listeners to suggestion accordion headers
    const suggestionHeaders = document.querySelectorAll('.suggestions .accordion-header');
    suggestionHeaders.forEach(header => {
        header.addEventListener('click', toggleAccordion);
    });
    
    // Download Report
    downloadReportBtn.addEventListener('click', function() {
        if (!currentAnalysis) {
            alert('No analysis data available.');
            return;
        }
        
        // Get the result ID from the current analysis
        const resultId = currentAnalysis.result_id;
        
        if (!resultId) {
            // Fallback to JSON if no result ID is available
            // Create a formatted report
            const report = {
                timestamp: new Date().toISOString(),
                ats_score: currentAnalysis.ats_score,
                suggestions: currentAnalysis.suggestions
            };
            
            // Convert to JSON and create download link
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", "resume_analysis_report.json");
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        } else {
            // Download PDF report
            window.location.href = `/download-pdf/${resultId}`;
        }
    });
    
    // Analyze New Resume
    analyzeNewBtn.addEventListener('click', function() {
        // Reset form
        resumeForm.reset();
        resetFileInput();
        
        // Show upload section
        uploadSection.style.display = 'block';
        resultsSection.style.display = 'none';
        
        // Clear current analysis
        currentAnalysis = null;
    });
});