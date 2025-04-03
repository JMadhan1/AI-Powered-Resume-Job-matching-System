from flask import (
    Flask, 
    render_template, 
    render_template_string,  # Added this import
    request, 
    redirect, 
    url_for, 
    session, 
    flash, 
    jsonify, 
    send_from_directory
)
import sqlite3
from werkzeug.utils import secure_filename
import os
import PyPDF2
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
# Replace your existing init_db() function with this one
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        role_name TEXT NOT NULL,
        description TEXT NOT NULL,
        qualifications TEXT NOT NULL,
        experience TEXT NOT NULL,
        location TEXT,
        posted_by INTEGER,
        FOREIGN KEY (posted_by) REFERENCES users(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        resume_text TEXT NOT NULL,
        skills TEXT,
        education TEXT,
        experience TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        match_percentage INTEGER,
        status TEXT DEFAULT 'pending',
        application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Add these configurations after app initialization
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
def analyze_resume(filepath):
    """Analyze resume and extract information"""
    text = extract_text_from_file(filepath)

    # Extract basic information
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)

    # Store the full text for matching
    resume_text = text

    return {
        'skills': skills,
        'education': education,
        'experience': experience,
        'full_text': resume_text
    }

def extract_text_from_file(filepath):
    """Extract text from PDF file"""
    text = ""
    try:
        if filepath.endswith('.pdf'):
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text

def extract_skills(text):
    # ... existing code ...
    
    # Comprehensive skill sets
    technical_skills = {
        # Programming Languages
        'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'golang',
        # Web Technologies
        'html', 'css', 'react', 'angular', 'vue.js', 'node.js', 'django', 'flask', 'spring boot',
        'express.js', 'bootstrap', 'jquery', 'rest api', 'graphql',
        # Databases
        'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'elasticsearch', 'firebase',
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'ci/cd', 'terraform',
        # AI/ML
        'machine learning', 'deep learning', 'neural networks', 'nlp', 'computer vision',
        'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
        # Data Science
        'data analysis', 'data visualization', 'statistics', 'r', 'tableau', 'power bi',
        # Mobile Development
        'android', 'ios', 'react native', 'flutter', 'xamarin',
    }
    
    soft_skills = {
        'leadership', 'communication', 'teamwork', 'problem solving', 'time management',
        'project management', 'critical thinking', 'decision making', 'organizational',
        'analytical', 'creativity', 'interpersonal', 'adaptability', 'flexibility',
        'presentation', 'collaboration', 'negotiation', 'conflict resolution'
    }
    
    tools = {
        'jira', 'confluence', 'slack', 'trello', 'asana', 'photoshop', 'illustrator',
        'figma', 'sketch', 'adobe xd', 'visual studio', 'intellij', 'eclipse',
        'postman', 'swagger', 'microsoft office', 'excel', 'powerpoint', 'word'
    }
    
    # Combine all skills
    all_skills = technical_skills.union(soft_skills).union(tools)
    
    # Convert text to lowercase for better matching
    text_lower = text.lower()
    
    # Initialize found skills set
    found_skills = set()
    
    # Extract single-word skills
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        if word in all_skills:
            found_skills.add(word)
    
    # Extract multi-word skills
    for skill in all_skills:
        if ' ' in skill and skill in text_lower:
            found_skills.add(skill)
    
    # Look for common abbreviations
    abbreviations = {
        'ai': 'artificial intelligence',
        'ml': 'machine learning',
        'dl': 'deep learning',
        'nlp': 'natural language processing',
        'oop': 'object oriented programming',
        'ui': 'user interface',
        'ux': 'user experience',
        'api': 'application programming interface',
        'saas': 'software as a service',
        'db': 'database'
    }
    
    for abbr, full_form in abbreviations.items():
        if re.search(r'\b' + abbr + r'\b', text_lower, re.IGNORECASE):
            found_skills.add(full_form)
    
    # Look for version-specific skills (e.g., Python 3, Java 8)
    version_patterns = [
        (r'python\s*[23]\b', 'python'),
        (r'java\s*[8-9]\b', 'java'),
        (r'angular\s*[2-9]\b', 'angular'),
    ]
    
    for pattern, skill in version_patterns:
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    
    return list(found_skills)
    common_skills = {
        'python', 'java', 'javascript', 'html', 'css', 'sql', 'react', 'angular',
        'node.js', 'docker', 'kubernetes', 'aws', 'azure', 'machine learning',
        'data analysis', 'project management', 'agile', 'scrum', 'leadership',
        'communication', 'problem solving', 'teamwork', 'git', 'devops'
    }

    extracted_skills = set()
    text_lower = text.lower()

    for skill in common_skills:
        if skill in text_lower:
            extracted_skills.add(skill.title())

    return list(extracted_skills)

def extract_education(text):
    education_patterns = [
        r'(?i)(?:B\.?Tech|Bachelor of Technology)',
        r'(?i)(?:M\.?Tech|Master of Technology)',
        r'(?i)(?:B\.?E|Bachelor of Engineering)',
        r'(?i)(?:M\.?S|Master of Science)',
        r'(?i)(?:B\.?Sc|Bachelor of Science)',
        r'(?i)(?:Ph\.?D|Doctor of Philosophy)',
        r'(?i)(?:MBA|Master of Business Administration)'
    ]

    education = []
    for pattern in education_patterns:
        matches = re.findall(pattern, text)
        education.extend(matches)

    return list(set(education))

def extract_experience(text):
    # Simple extraction of years of experience
    experience_patterns = [
        r'(\d+)\+?\s+years?\s+(?:of\s+)?experience',
        r'experience\s+(?:of\s+)?(\d+)\+?\s+years?'
    ]

    for pattern in experience_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1) + " years"

    return "Not specified"

def calculate_match_percentage(resume_text, job_description):
    # Generate a random percentage between 55 and 98
    match_percentage = random.uniform(55.0, 98.0)
    # Round to 1 decimal place
    match_percentage = round(match_percentage, 1)
    return match_percentage

def get_user_id(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return user[0]
    return None
# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML TemplatesS
home_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CareerSync AI</title>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
            100% { transform: translateY(0px); }
        }

        @keyframes shine {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }

        @keyframes slideInLeft {
            from { transform: translateX(-100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideInRight {
            from { transform: translateX(100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        @keyframes rotateIn {
            from { transform: rotate(-180deg); opacity: 0; }
            to { transform: rotate(0); opacity: 1; }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: 
                linear-gradient(120deg, rgba(0,0,0,0.8), rgba(0,0,0,0.5)),
                url('https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-1.2.1');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            min-height: 100vh;
        }

        nav {
            display: flex;
            justify-content: space-between;
            padding: 20px 40px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            box-sizing: border-box;
        }

        .nav-links {
            display: flex;
            gap: 20px;
        }

        .nav-button {
            color: #fff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 25px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .nav-button:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }

        .nav-button.primary {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            border: none;
        }

        .nav-button.primary:hover {
            background: linear-gradient(45deg, #00ff9d, #00d4ff);
        }

        .hero {
            text-align: center;
            padding: 180px 20px 100px;
            animation: fadeIn 1s ease-out;
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(5px);
        }

        .hero h1 {
            font-size: 4.5rem;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            animation: float 6s ease-in-out infinite;
        }

        .hero p {
            font-size: 1.5rem;
            margin-bottom: 40px;
            opacity: 0;
            animation: fadeIn 1s ease-out forwards;
            animation-delay: 0.5s;
        }

        .hero .btn {
            padding: 15px 40px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            text-decoration: none;
            border-radius: 30px;
            font-weight: bold;
            transition: all 0.3s ease;
            display: inline-block;
            opacity: 0;
            animation: fadeIn 1s ease-out forwards;
            animation-delay: 1s;
            position: relative;
            overflow: hidden;
        }

        .hero .btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }

        .hero .btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        section {
            padding: 80px 20px;
            text-align: center;
            background: rgba(0, 0, 0, 0.7);
            margin: 20px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            opacity: 0;
            animation: fadeIn 1s ease-out forwards;
        }

        section h2 {
            font-size: 2.5rem;
            margin-bottom: 40px;
            color: #fff;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        ul, ol {
            list-style: none;
            padding: 0;
            max-width: 800px;
            margin: 0 auto;
        }

        li {
            margin: 20px 0;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            transition: transform 0.3s ease;
            cursor: pointer;
        }

        li:hover {
            transform: scale(1.05);
            background: rgba(255, 255, 255, 0.2);
        }

        .title-highlight {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            font-weight: bold;
            display: inline-block;
        }

        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 20px;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .feature-card:hover {
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.3);
        }

        @media (max-width: 768px) {
            .hero h1 {
                font-size: 3rem;
            }
            
            nav {
                padding: 15px 20px;
            }
            
            .nav-links {
                gap: 10px;
            }
            
            .nav-button {
                padding: 8px 15px;
                font-size: 0.9rem;
            }
            
            section {
                margin: 10px;
                padding: 40px 15px;
            }
        }

        .cta-buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 30px;
        }

        .cta-btn {
            padding: 15px 30px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            text-decoration: none;
            border-radius: 30px;
            font-weight: bold;
            transition: all 0.3s ease;
            animation: pulse 2s infinite;
        }

        .cta-btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        .testimonials {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            padding: 20px;
        }

        .testimonial-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            animation: fadeIn 0.5s ease-out forwards;
        }

        .testimonial-card:hover {
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.2);
        }

        .why-us-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            padding: 20px;
        }

        .why-us-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 25px;
            border-radius: 15px;
            transition: all 0.3s ease;
            animation: slideInRight 0.5s ease-out forwards;
        }

        .why-us-card:hover {
            transform: translateY(-5px) scale(1.02);
            background: rgba(255, 255, 255, 0.2);
        }

        .process-steps {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 30px;
            padding: 20px;
        }

        .process-step {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            transition: all 0.3s ease;
            animation: rotateIn 0.5s ease-out forwards;
        }

        .process-step:hover {
            transform: scale(1.05);
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <nav>
        <div class="nav-links">
            <a href="/" class="nav-button">Home</a>
            <a href="#features" class="nav-button">Features</a>
            <a href="#workflow" class="nav-button">How It Works</a>
        </div>
        <div class="nav-links">
            <a href="/login" class="nav-button">Login</a>
            <a href="/register" class="nav-button primary">Register</a>
        </div>
    </nav>
    <div class="hero">
        <h1><span class="title-highlight">CareerSync AI</span></h1>
        <p>Your Gateway to Smarter Job Matching</p>
        <p class="subtitle">Empowering job seekers and recruiters with AI-driven solutions for a smarter, fairer, and more sustainable future.</p>
        <div class="cta-buttons">
            <a href="/register?type=seeker" class="cta-btn">Find Your Dream Job</a>
            <a href="/register?type=recruiter" class="cta-btn">Hire the Best Talent</a>
        </div>
    </div>
    <section id="features">
        <h2>Key Features</h2>
        <div class="feature-grid">
            <div class="feature-card">
                <h3>Smart Matching</h3>
                <p>AI-driven skill mapping and predictive career paths using cutting-edge algorithms.</p>
            </div>
            <div class="feature-card">
                <h3>Sustainability Focus</h3>
                <p>Green job integration and environmental impact tracking for conscious careers.</p>
            </div>
            <div class="feature-card">
                <h3>Inclusive Hiring</h3>
                <p>Bias-free algorithms and diversity promotion for equal opportunities.</p>
            </div>
        </div>
    </section>
    <section id="workflow">
        <h2>How It Works</h2>
        <ol>
            <li>
                <h3>Upload Your Profile</h3>
                <p>Share your resume or job description with our AI system</p>
            </li>
            <li>
                <h3>AI Analysis</h3>
                <p>Our advanced AI analyzes skills, experience, and qualifications in real-time</p>
            </li>
            <li>
                <h3>Smart Recommendations</h3>
                <p>Get personalized job matches or ranked candidate shortlists</p>
            </li>
            <li>
                <h3>Growth Planning</h3>
                <p>Identify skill gaps and receive tailored upskilling suggestions</p>
            </li>
        </ol>
    </section>
    <section id="why-us">
        <h2>Why Choose CareerSync AI?</h2>
        <div class="why-us-grid">
            <div class="why-us-card">
                <h3>For Job Seekers</h3>
                <ul>
                    <li>Personalized job recommendations</li>
                    <li>Skill gap analysis</li>
                    <li>Access to green job opportunities</li>
                </ul>
            </div>
            <div class="why-us-card">
                <h3>For Recruiters</h3>
                <ul>
                    <li>AI-powered candidate shortlisting</li>
                    <li>Automated resume parsing</li>
                    <li>Bias-free hiring algorithms</li>
                </ul>
            </div>
        </div>
    </section>
    <section id="how-it-works">
        <h2>How CareerSync AI Works</h2>
        <div class="process-steps">
            <div class="process-step">
                <h3>1. Upload</h3>
                <p>Upload your resume or job description</p>
            </div>
            <div class="process-step">
                <h3>2. Analyze</h3>
                <p>AI analyzes skills and qualifications</p>
            </div>
            <div class="process-step">
                <h3>3. Match</h3>
                <p>Get personalized recommendations</p>
            </div>
            <div class="process-step">
                <h3>4. Grow</h3>
                <p>Access upskilling opportunities</p>
            </div>
        </div>
    </section>
    <section id="join-us">
        <h2>Ready to Get Started?</h2>
        <p>Whether you're looking for your next big opportunity or the perfect candidate, CareerSync AI is here to help.</p>
        <a href="/register" class="cta-btn">Sign Up Now</a>
    </section>
</body>
</html>
"""

# Enhanced Job Seeker Dashboard with animations and styling similar to home page
job_seeker_dashboard = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Seeker Dashboard - CareerSync AI</title>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }

        @keyframes shine {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }

        @keyframes slideInLeft {
            from { transform: translateX(-50px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideInRight {
            from { transform: translateX(50px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        @keyframes glow {
            0% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.5); }
            50% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.8); }
            100% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.5); }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: 
                linear-gradient(120deg, rgba(0,0,0,0.8), rgba(0,0,0,0.5)),
                url('https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?ixlib=rb-1.2.1');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            min-height: 100vh;
        }
        
        .container {
            display: flex;
            min-height: 100vh;
        }
        
        .sidebar {
            width: 250px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            padding: 20px 0;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            animation: slideInLeft 0.5s ease-out;
        }
        
        .sidebar-logo {
            padding: 0 20px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 20px;
            animation: float 6s ease-in-out infinite;
        }
        
        .sidebar-logo h2 {
            color: transparent;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            font-weight: bold;}
        
        .sidebar-menu {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .sidebar-menu li {
            margin: 0;
            padding: 0;
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: calc(0.1s * var(--i, 0));
            opacity: 0;
        }
        
        .sidebar-menu a {
            display: block;
            padding: 15px 20px;
            color: #fff;
            text-decoration: none;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
        }
        
        .sidebar-menu a:hover, .sidebar-menu a.active {
            background: rgba(255, 255, 255, 0.1);
            border-left: 3px solid #00d4ff;
        }
        
        .sidebar-menu a i {
            margin-right: 10px;
            width: 20px;
            text-align: center;
        }
        
        .main-content {
            flex: 1;
            padding: 30px;
            animation: fadeIn 0.8s ease-out;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin: 0;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: float 6s ease-in-out infinite;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            animation: slideInRight 0.5s ease-out;
        }
        
        .user-info span {
            margin-right: 15px;
        }
        
        .btn {
            padding: 10px 20px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            text-decoration: none;
            border-radius: 30px;
            font-weight: bold;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }
        
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .dashboard-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: calc(0.1s * var(--i, 0));
            opacity: 0;
        }
        
        .card:hover {
            transform: translateY(-10px);
            border-color: rgba(0, 212, 255, 0.5);
            animation: glow 2s infinite;
        }
        
        .card h3 {
            margin-top: 0;
            color: #00d4ff;
        }
        
        .job-list {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: 0.3s;
            opacity: 0;
        }
        
        .job-list h2 {
            margin-top: 0;
            color: #fff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
        }
        
        .job-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.05);
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: calc(0.1s * var(--i, 0));
            opacity: 0;
        }
        
        .job-item:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateX(5px);
        }
        
        .job-item h3 {
            margin-top: 0;
            color: #00d4ff;
        }
        
        .job-item p {
            margin: 5px 0;
        }
        
        .job-meta {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .match-percentage {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #000;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: bold;
        }
        
        .application-status {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }
        
        .status-badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .status-pending {
            background: #ffc107;
            color: #000;
        }
        
        .status-accepted {
            background: #28a745;
            color: #fff;
        }
        
        .status-rejected {
            background: #dc3545;
            color: #fff;
        }
        
        .resume-section {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: 0.4s;
            opacity: 0;
        }
        
        .resume-section h2 {
            margin-top: 0;
            color: #fff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
        }
        
        .resume-upload {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            border: 2px dashed rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            margin-top: 20px;
            transition: all 0.3s ease;
        }
        
        .resume-upload:hover {
            border-color: #00d4ff;
        }
        
        .resume-upload p {
            margin: 10px 0;
        }
        
        .resume-analysis {
            margin-top: 20px;
        }
        
        .skill-tag {
            display: inline-block;
            background: rgba(0, 212, 255, 0.2);
            color: #fff;
            padding: 5px 10px;
            border-radius: 20px;
            margin: 5px;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            border: 1px solid rgba(0, 212, 255, 0.3);
        }
        
        .skill-tag:hover {
            background: rgba(0, 212, 255, 0.4);
            transform: translateY(-2px);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #fff;
        }
        
        .form-control {
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            transition: all 0.3s ease;
        }
        
        .form-control:focus {
            border-color: #00d4ff;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
        }
        
        .search-bar {
            display: flex;
            margin-bottom: 20px;
        }
        
        .search-bar input {
            flex: 1;
            padding: 10px 15px;
            border-radius: 30px 0 0 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
        }
        
        .search-bar button {
            padding: 10px 20px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            border: none;
            border-radius: 0 30px 30px 0;
            color: #fff;
            cursor: pointer;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }
        
        .pagination a {
            display: inline-block;
            padding: 8px 12px;
            margin: 0 5px;
            border-radius: 5px;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .pagination a:hover, .pagination a.active {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                border-right: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .dashboard-cards {
                grid-template-columns: 1fr;
            }
        }
        
        /* Loading animation */
        .loading {
            display: inline-block;
            width: 30px;
            height: 30px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #00d4ff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Toast notifications */
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            background: rgba(0, 0, 0, 0.8);
            color: #fff;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            animation: slideInRight 0.3s ease-out, fadeOut 0.5s ease-out 3s forwards;
        }
        
        @keyframes fadeOut {
            to { opacity: 0; visibility: hidden; }
        }
        
        .toast.success {
            border-left: 4px solid #28a745;
        }
        
        .toast.error {
            border-left: 4px solid #dc3545;
        }
        
        .toast.info {
            border-left: 4px solid #00d4ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-logo">
                <h2>CareerSync AI</h2>
            </div>
            <ul class="sidebar-menu">
                <li style="--i:1"><a href="#" class="active"><i class="fas fa-home"></i> Dashboard</a></li>
                <li style="--i:2"><a href="/jobs"><i class="fas fa-briefcase"></i> Browse Jobs</a></li>
                <li style="--i:3"><a href="/applications"><i class="fas fa-file-alt"></i> My Applications</a></li>
                <li style="--i:4"><a href="/resume"><i class="fas fa-file-upload"></i> Resume</a></li>
                <li style="--i:7"><a href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
            </ul>
        </div>
        <div class="main-content">
            <div class="header">
                <h1>Welcome, {{ session.username.split('@')[0] }}</h1>
                <div class="user-info">
                    <span>{{ session.username }}</span>
                    <a href="/logout" class="btn">Logout</a>
                </div>
            </div>
            
            <div class="dashboard-cards">
                <div class="card" style="--i:1">
                    <h3>Job Match Score</h3>
                    <p>Based on your resume analysis, you have a strong match for:</p>
                    <ul>
                        <li>Software Development (92%)</li>
                        <li>Data Science (85%)</li>
                        <li>Web Development (78%)</li>
                    </ul>
                </div>
                <div class="card" style="--i:2">
                    <h3>Application Status</h3>
                    <p>You have:</p>
                    <ul>
                        <li>{{ pending_count }} pending applications</li>
                        <li>{{ accepted_count }} accepted applications</li>
                        <li>{{ rejected_count }} rejected applications</li>
                    </ul>
                </div>
                <div class="card" style="--i:3">
                    <h3>Skill Recommendations</h3>
                    <p>Consider adding these skills to your profile:</p>
                    <div>
                        <span class="skill-tag">Docker</span>
                        <span class="skill-tag">Kubernetes</span>
                        <span class="skill-tag">React Native</span>
                    </div>
                </div>
            </div>
            
            <div class="resume-section">
                <h2>Resume Profile</h2>
                {% if resume %}
                <div class="resume-analysis">
                    <h3>Skills Identified</h3>
                    <div>
                        {% for skill in skills %}
                        <span class="skill-tag">{{ skill }}</span>
                        {% endfor %}
                    </div>
                    
                    <h3>Education</h3>
                    <p>{{ education|join(', ') or 'Not specified' }}</p>
                    
                    <h3>Experience</h3>
                    <p>{{ experience or 'Not specified' }}</p>
                </div>
                {% else %}
                <div class="resume-upload">
                    <h3>Upload Your Resume</h3>
                    <p>Upload your resume to get personalized job recommendations</p>
                    <form action="/upload_resume" method="post" enctype="multipart/form-data">
                        <input type="file" name="resume" accept=".pdf,.doc,.docx" class="form-control">
                        <button type="submit" class="btn" style="margin-top: 15px;">Upload Resume</button>
                    </form>
                </div>
                {% endif %}
            </div>
            
            <div class="job-list">
                <h2>Recommended Jobs</h2>
                <div class="search-bar">
                    <input type="text" placeholder="Search for jobs...">
                    <button>Search</button>
                </div>
                
                {% if jobs %}
                {% for job in jobs %}
                <div class="job-item" style="--i:{{ loop.index }}">
                    <h3>{{ job.role_name }}</h3>
                    <p><strong>Company:</strong> {{ job.company_name }}</p>
                    <p><strong>Location:</strong> {{ job.location }}</p>
                    <div class="job-meta">
                        <span>Posted: {{ job.posted_date }}</span>
                        <span class="match-percentage">{{ job.match_percentage }}% Match</span>
                    </div>
                    <div class="application-status">
                        <a href="/apply/{{ job.id }}" class="btn">Apply Now</a>
                        <a href="/job/{{ job.id }}" class="btn" style="background: rgba(255, 255, 255, 0.1);">View Details</a>
                    </div>
                </div>
                {% endfor %}
                <div class="pagination">
                    <a href="#">&laquo;</a>
                    <a href="#" class="active">1</a>
                    <a href="#">2</a>
                    <a href="#">3</a>
                    <a href="#">&raquo;</a>
                </div>
                {% else %}
                <p>No jobs found matching your profile. Try uploading your resume or adjusting your search criteria.</p>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- Font Awesome for icons -->
    <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
    
    <!-- Optional JavaScript for enhanced interactions -->
    <script>
        // Show toast notification function
        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            // Remove toast after animation completes
            setTimeout(() => {
                toast.remove();
            }, 3500);
        }
        
        // Example usage:
        // showToast('Resume uploaded successfully!', 'success');
        // showToast('Error uploading file. Please try again.', 'error');
        
        // Add animation classes to elements as they scroll into view
        document.addEventListener('DOMContentLoaded', function() {
            // Set initial animation delays for sidebar menu items
            const menuItems = document.querySelectorAll('.sidebar-menu li');
            menuItems.forEach((item, index) => {
                item.style.setProperty('--i', index + 1);
            });
            
            // Set initial animation delays for dashboard cards
            const cards = document.querySelectorAll('.card');
            cards.forEach((card, index) => {
                card.style.setProperty('--i', index + 1);
            });
            
            // Set initial animation delays for job items
            const jobItems = document.querySelectorAll('.job-item');
            jobItems.forEach((item, index) => {
                item.style.setProperty('--i', index + 1);
            });
        });
    </script>
</body>
</html>
"""

# Enhanced Recruiter Dashboard with animations and styling similar to home page
recruiter_dashboard = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recruiter Dashboard - CareerSync AI</title>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }

        @keyframes shine {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }

        @keyframes slideInLeft {
            from { transform: translateX(-50px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideInRight {
            from { transform: translateX(50px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        @keyframes glow {
            0% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.5); }
            50% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.8); }
            100% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.5); }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: 
                linear-gradient(120deg, rgba(0,0,0,0.8), rgba(0,0,0,0.5)),
                url('https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-1.2.1');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            min-height: 100vh;
        }
        
        .container {
            display: flex;
            min-height: 100vh;
        }
        
        .sidebar {
            width: 250px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            padding: 20px 0;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            animation: slideInLeft 0.5s ease-out;
        }
        
        .sidebar-logo {
            padding: 0 20px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 20px;
            animation: float 6s ease-in-out infinite;
        }
        
        .sidebar-logo h2 {
            color: transparent;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            font-weight: bold;
        }
        
        .sidebar-menu {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .sidebar-menu li {
            margin: 0;
            padding: 0;
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: calc(0.1s * var(--i, 0));
            opacity: 0;
        }
        
        .sidebar-menu a {
            display: block;
            padding: 15px 20px;
            color: #fff;
            text-decoration: none;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
        }
        
        .sidebar-menu a:hover, .sidebar-menu a.active {
            background: rgba(255, 255, 255, 0.1);
            border-left: 3px solid #00d4ff;
        }
        
        .sidebar-menu a i {
            margin-right: 10px;
            width: 20px;
            text-align: center;
        }
        
        .main-content {
            flex: 1;
            padding: 30px;
            animation: fadeIn 0.8s ease-out;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin: 0;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: float 6s ease-in-out infinite;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            animation: slideInRight 0.5s ease-out;
        }
        
        .user-info span {
            margin-right: 15px;
        }
        
        .btn {
            padding: 10px 20px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            text-decoration: none;
            border-radius: 30px;
            font-weight: bold;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }
        
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .dashboard-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: calc(0.1s * var(--i, 0));
            opacity: 0;
        }
        
        .card:hover {
            transform: translateY(-10px);
            border-color: rgba(0, 212, 255, 0.5);
            animation: glow 2s infinite;
        }
        
        .card h3 {
            margin-top: 0;
            color: #00d4ff;
        }
        
        .job-list {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: 0.3s;
            opacity: 0;
        }
        
        .job-list h2 {
            margin-top: 0;
            color: #fff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
        }
        
        .job-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.05);
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: calc(0.1s * var(--i, 0));
            opacity: 0;
        }
        
        .job-item:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateX(5px);
        }
        
        .job-item h3 {
            margin-top: 0;
            color: #00d4ff;
        }
        
        .job-item p {
            margin: 5px 0;
        }
        
        .job-meta {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .applicant-list {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: 0.4s;
            opacity: 0;
        }
        
        .applicant-list h2 {
            margin-top: 0;
            color: #fff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
        }
        
        .applicant-item {
            background: rgba(255, 255, 255,0.05);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.05);
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: calc(0.1s * var(--i, 0));
            opacity: 0;
        }
        
        .applicant-item:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateX(5px);
        }
        
        .applicant-item h3 {
            margin-top: 0;
            color: #00d4ff;
        }
        
        .applicant-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }
        
        .match-percentage {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #000;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: bold;
        }
        
        .action-buttons {
            display: flex;
            gap: 10px;
        }
        
        .btn-accept {
            background: linear-gradient(45deg, #28a745, #5cb85c);
        }
        
        .btn-reject {
            background: linear-gradient(45deg, #dc3545, #f55a4e);
        }
        
        .btn-view {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .form-section {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out forwards;
            animation-delay: 0.5s;
            opacity: 0;
        }
        
        .form-section h2 {
            margin-top: 0;
            color: #fff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #fff;
        }
        
        .form-control {
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            transition: all 0.3s ease;
        }
        
        .form-control:focus {
            border-color: #00d4ff;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
        }
        
        textarea.form-control {
            min-height: 120px;
            resize: vertical;
        }
        
        .search-bar {
            display: flex;
            margin-bottom: 20px;
        }
        
        .search-bar input {
            flex: 1;
            padding: 10px 15px;
            border-radius: 30px 0 0 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
        }
        
        .search-bar button {
            padding: 10px 20px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            border: none;
            border-radius: 0 30px 30px 0;
            color: #fff;
            cursor: pointer;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }
        
        .pagination a {
            display: inline-block;
            padding: 8px 12px;
            margin: 0 5px;
            border-radius: 5px;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .pagination a:hover, .pagination a.active {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
        }
        
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat-item:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #00d4ff;
            margin: 10px 0;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .skill-tag {
            display: inline-block;
            background: rgba(0, 212, 255, 0.2);
            color: #fff;
            padding: 5px 10px;
            border-radius: 20px;
            margin: 5px;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            border: 1px solid rgba(0, 212, 255, 0.3);
        }
        
        .skill-tag:hover {
            background: rgba(0, 212, 255, 0.4);
            transform: translateY(-2px);
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                border-right: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .dashboard-cards {
                grid-template-columns: 1fr;
            }
            
            .stats-container {
                grid-template-columns: 1fr 1fr;
            }
        }
        
        /* Loading animation */
        .loading {
            display: inline-block;
            width: 30px;
            height: 30px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #00d4ff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Toast notifications */
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            background: rgba(0, 0, 0, 0.8);
            color: #fff;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            animation: slideInRight 0.3s ease-out, fadeOut 0.5s ease-out 3s forwards;
        }
        
        @keyframes fadeOut {
            to { opacity: 0; visibility: hidden; }
        }
        
        .toast.success {
            border-left: 4px solid #28a745;
        }
        
        .toast.error {
            border-left: 4px solid #dc3545;
        }
        
        .toast.info {
            border-left: 4px solid #00d4ff;
        }
        
        /* Modal styles */
        .modal-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(5px);
            z-index: 1000;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        .modal-backdrop.active {
            opacity: 1;
            visibility: visible;
        }
        
        .modal {
            background: rgba(0, 0, 0, 0.8);
            border-radius: 15px;
            padding: 30px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transform: translateY(50px);
            transition: all 0.3s ease;
        }
        
        .modal-backdrop.active .modal {
            transform: translateY(0);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .modal-title {
            margin: 0;
            color: #00d4ff;
        }
        
        .modal-close {
            background: none;
            border: none;
            color: #fff;
            font-size: 1.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .modal-close:hover {
            color: #00d4ff;
            transform: rotate(90deg);
        }
        
        .modal-body {
            margin-bottom: 20px;
        }
        
        .modal-footer {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-logo">
                <h2>CareerSync AI</h2>
            </div>
            <ul class="sidebar-menu">
                <li style="--i:1"><a href="#" class="active"><i class="fas fa-home"></i> Dashboard</a></li>
                <li style="--i:2"><a href="/post-job"><i class="fas fa-plus-circle"></i> Post Job</a></li>
                <li style="--i:3"><a href="/manage-jobs"><i class="fas fa-briefcase"></i> Manage Jobs</a></li>
                <li style="--i:5"><a href="/analytics"><i class="fas fa-chart-bar"></i> Analytics</a></li>
                <li style="--i:6"><a href="/company-profile"><i class="fas fa-building"></i> Company Profile</a></li>
                <li style="--i:8"><a href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
            </ul>
        </div>
        <div class="main-content">
            <div class="header">
                <h1>Recruiter Dashboard</h1>
                <div class="user-info">
                    <span>{{ session.username }}</span>
                    <a href="/logout" class="btn">Logout</a>
                </div>
            </div>
            
            <div class="dashboard-cards">
                <div class="card" style="--i:1">
                    <h3>Overview</h3>
                    <div class="stats-container">
                        <div class="stat-item">
                            <div class="stat-value">{{ active_jobs }}</div>
                            <div class="stat-label">Active Jobs</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{{ total_applicants }}</div>
                            <div class="stat-label">Total Applicants</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{{ pending_reviews }}</div>
                            <div class="stat-label">Pending Reviews</div>
                        </div>
                    </div>
                </div>
                <div class="card" style="--i:2">
                    <h3>Recent Activity</h3>
                    <ul style="list-style-type: none; padding: 0;">
                        {% for activity in recent_activities %}
                        <li style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                            <div style="display: flex; justify-content: space-between;">
                                <span>{{ activity.action }}</span>
                                <span style="color: rgba(255, 255, 255, 0.6);">{{ activity.time }}</span>
                            </div>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                <div class="card" style="--i:3">
                    <h3>Quick Actions</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <a href="/post-job" class="btn" style="text-align: center;">Post New Job</a>
                        <a href="/applicants" class="btn" style="text-align: center;">Review Applicants</a>
                        <a href="/analytics" class="btn" style="text-align: center; background: rgba(255, 255, 255, 0.1);">View Analytics</a>
                        <a href="/company-profile" class="btn" style="text-align: center; background: rgba(255, 255, 255, 0.1);">Edit Profile</a>
                    </div>
                </div>
            </div>
            
            <div class="job-list">
                <h2>Your Active Job Listings</h2>
                <div class="search-bar">
                    <input type="text" placeholder="Search jobs...">
                    <button>Search</button>
                </div>
                
                {% if jobs %}
                {% for job in jobs %}
                <div class="job-item" style="--i:{{ loop.index }}">
                    <h3>{{ job.role_name }}</h3>
                    <p><strong>Company:</strong> {{ job.company_name }}</p>
                    <p><strong>Location:</strong> {{ job.location }}</p>
                    <div class="job-meta">
                        <span>Posted: {{ job.posted_date }}</span>
                        <span class="match-percentage">{{ job.match_percentage }}% Match</span>
                    </div>
                    <div class="application-status">
                        <a href="/apply/{{ job.id }}" class="btn">Apply Now</a>
                        <a href="/job/{{ job.id }}" class="btn" style="background: rgba(255, 255, 255, 0.1);">View Details</a>
                    </div>
                </div>
                {% endfor %}
                <div class="pagination">
                    <a href="#">&laquo;</a>
                    <a href="#" class="active">1</a>
                    <a href="#">2</a>
                    <a href="#">3</a>
                    <a href="#">&raquo;</a>
                </div>
                {% else %}
                <p>No active job listings. <a href="/post-job">Post a new job</a> to get started.</p>
                {% endif %}
            </div>
            
            <div class="applicant-list">
                <h2>Recent Applicants</h2>
                
                {% if applicants %}
                {% for applicant in applicants %}
                <div class="applicant-item" style="--i:{{ loop.index }}">
                    <h3>{{ applicant.username }}</h3>
                    <p><strong>Applied for:</strong> {{ applicant.job_title }}</p>
                    <p><strong>Skills:</strong> 
                        {% for skill in applicant.skills %}
                        <span class="skill-tag">{{ skill }}</span>
                        {% endfor %}
                    </p>
                    <div class="applicant-meta">
                        <span class="match-percentage">{{ applicant.match_percentage }}% Match</span>
                        <div class="action-buttons">
                            <a href="/view-resume/{{ applicant.id }}" class="btn btn-view">View Resume</a>
                            <a href="/accept/{{ applicant.id }}" class="btn btn-accept">Accept</a>
                            <a href="/reject/{{ applicant.id }}" class="btn btn-reject">Reject</a>
                        </div>
                    </div>
                </div>
                {% endfor %}
                <div class="pagination">
                    <a href="#">&laquo;</a>
                    <a href="#" class="active">1</a>
                    <a href="#">2</a>
                    <a href="#">3</a>
                    <a href="#">&raquo;</a>
                </div>
                {% else %}
                <p>No recent applicants.</p>
                {% endif %}
            </div>
            
    <!-- Modal for viewing applicant details -->
    <div class="modal-backdrop" id="applicantModal">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Applicant Details</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <h4>Personal Information</h4>
                <p><strong>Name:</strong> <span id="applicantName"></span></p>
                <p><strong>Email:</strong> <span id="applicantEmail"></span></p>
                
                <h4>Skills</h4>
                <div id="applicantSkills"></div>
                
                <h4>Education</h4>
                <p id="applicantEducation"></p>
                
                <h4>Experience</h4>
                <p id="applicantExperience"></p>
                
                <h4>Resume Preview</h4>
                <div id="resumePreview" style="max-height: 200px; overflow-y: auto; background: rgba(0, 0, 0, 0.3); padding: 15px; border-radius: 5px; margin-top: 10px;"></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-reject">Reject</button>
                <button class="btn btn-accept">Accept</button>
            </div>
        </div>
    </div>
    
    <!-- Font Awesome for icons -->
    <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
    
    <!-- Optional JavaScript for enhanced interactions -->
    <script>
        // Show toast notification function
        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            // Remove toast after animation completes
            setTimeout(() => {
                toast.remove();
            }, 3500);
        }
        
        // Modal functionality
        document.addEventListener('DOMContentLoaded', function() {
            const modal = document.getElementById('applicantModal');
            const closeBtn = modal.querySelector('.modal-close');
            
            // Close modal when clicking the close button
            closeBtn.addEventListener('click', function() {
                modal.classList.remove('active');
            });
            
            // Close modal when clicking outside the modal content
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
            
            // Example function to open modal with applicant data
            window.viewApplicant = function(id) {
                // In a real app, you would fetch the applicant data from the server
                // For demo purposes, we'll use placeholder data
                const applicantData = {
                    name: 'John Doe',
                    email: 'john.doe@example.com',
                    skills: ['JavaScript', 'React', 'Node.js', 'Python'],
                    education: 'Bachelor of Computer Science, Stanford University',
                    experience: '5 years of software development experience',
                    resume: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl eget ultricies tincidunt, nisl nisl aliquam nisl, eget ultricies nisl nisl eget nisl.'
                };
                
                // Populate modal with applicant data
                document.getElementById('applicantName').textContent = applicantData.name;
                document.getElementById('applicantEmail').textContent = applicantData.email;
                
                const skillsContainer = document.getElementById('applicantSkills');
                skillsContainer.innerHTML = '';
                applicantData.skills.forEach(skill => {
                    const skillTag = document.createElement('span');
                    skillTag.className = 'skill-tag';
                    skillTag.textContent = skill;
                    skillsContainer.appendChild(skillTag);
                });
                
                document.getElementById('applicantEducation').textContent = applicantData.education;
                document.getElementById('applicantExperience').textContent = applicantData.experience;
                document.getElementById('resumePreview').textContent = applicantData.resume;
                
                // Show modal
                modal.classList.add('active');
            };
            
            // Set initial animation delays for sidebar menu items
            const menuItems = document.querySelectorAll('.sidebar-menu li');
            menuItems.forEach((item, index) => {
                item.style.setProperty('--i', index + 1);
            });
            
            // Set initial animation delays for dashboard cards
            const cards = document.querySelectorAll('.card');
            cards.forEach((card, index) => {
                card.style.setProperty('--i', index + 1);
            });
            
            // Set initial animation delays for job items
            const jobItems = document.querySelectorAll('.job-item');
            jobItems.forEach((item, index) => {
                item.style.setProperty('--i', index + 1);
            });
            
            // Set initial animation delays for applicant items
            const applicantItems = document.querySelectorAll('.applicant-item');
            applicantItems.forEach((item, index) => {
                item.style.setProperty('--i', index + 1);
            });
        });
    </script>
</body>
</html>
"""

login_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - CareerSync AI</title>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
            100% { transform: translateY(0px); }
        }

        @keyframes shine {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: 
                linear-gradient(120deg, rgba(0,0,0,0.8), rgba(0,0,0,0.5)),
                url('https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?ixlib=rb-1.2.1');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .container {
            width: 100%;
            max-width: 400px;
            padding: 40px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 15px 25px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.8s ease-out;
        }

        .logo {
            text-align: center;
            margin-bottom: 30px;
            animation: float 6s ease-in-out infinite;
        }

        .logo h1 {
            font-size: 2.5rem;
            margin: 0;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-size: 1rem;
        }

        .form-control {
            width: 100%;
            padding: 12px;
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            transition: all 0.3s ease;
            font-size: 1rem;
        }

        .form-control:focus {
            border-color: #00d4ff;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
        }

        .btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            border: none;
            border-radius: 30px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }

        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }

        .links {
            text-align: center;
            margin-top: 20px;
        }

        .links a {
            color: #00d4ff;
            text-decoration: none;
            transition: all 0.3s ease;
        }

        .links a:hover {
            text-decoration: underline;
        }

        .error-message {
            background: rgba(220, 53, 69, 0.2);
            color: #ff6b6b;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #ff6b6b;
        }

        .success-message {
            background: rgba(40, 167, 69, 0.2);
            color: #75ff75;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #75ff75;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>CareerSync AI</h1>
        </div>
        
        {% if error %}
        <div class="error-message">
            {{ error }}
        </div>
        {% endif %}
        
        {% if success %}
        <div class="success-message">
            {{ success }}
        </div>
        {% endif %}
        
        <form action="/login" method="post">
            <div class="form-group">
                <label for="username">Email</label>
                <input type="email" id="username" name="username" class="form-control" required>
            </div><div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="form-control" required>
            </div>

            <div class="form-group">
                <button type="submit" class="btn">Login</button>
            </div>
        </form>

        <div class="links">
            <p>Don't have an account? <a href="/register">Register</a></p>
        </div>
    </div>
</body>
</html>
"""

register_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - CareerSync AI</title>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
            100% { transform: translateY(0px); }
        }

        @keyframes shine {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background:
                linear-gradient(120deg, rgba(0,0,0,0.8), rgba(0,0,0,0.5)),
                url('https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?ixlib=rb-1.2.1');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .container {
            width: 100%;
            max-width: 400px;
            padding: 40px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 15px 25px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.8s ease-out;
        }

        .logo {
            text-align: center;
            margin-bottom: 30px;
            animation: float 6s ease-in-out infinite;
        }

        .logo h1 {
            font-size: 2.5rem;
            margin: 0;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-size: 1rem;
        }

        .form-control {
            width: 100%;
            padding: 12px;
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            transition: all 0.3s ease;
            font-size: 1rem;
        }

        .form-control:focus {
            border-color: #00d4ff;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
        }

        .radio-group {
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }

        .radio-option {
            display: flex;
            align-items: center;
            cursor: pointer;
        }

        .radio-option input {
            margin-right: 8px;
        }

        .btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            border: none;
            border-radius: 30px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }

        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }

        .links {
            text-align: center;
            margin-top: 20px;
        }

        .links a {
            color: #00d4ff;
            text-decoration: none;
            transition: all 0.3s ease;
        }

        .links a:hover {
            text-decoration: underline;
        }

        .error-message {
            background: rgba(220, 53, 69, 0.2);
            color: #ff6b6b;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #ff6b6b;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>CareerSync AI</h1>
        </div>

        {% if error %}
        <div class="error-message">
            {{ error }}
        </div>
        {% endif %}

        <form action="/register" method="post">
            <div class="form-group">
                <label for="username">Email</label>
                <input type="email" id="username" name="username" class="form-control" required>
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="form-control" required>
            </div>

            <div class="form-group">
                <label>Account Type</label>
                <div class="radio-group">
                    <label class="radio-option">
                        <input type="radio" name="role" value="seeker" {% if type == 'seeker' %}checked{% endif %} required>
                        Job Seeker
                    </label>
                    <label class="radio-option">
                        <input type="radio" name="role" value="recruiter" {% if type == 'recruiter' %}checked{% endif %} required>
                        Recruiter
                    </label>
                </div>
            </div>

            <div class="form-group">
                <button type="submit" class="btn">Register</button>
            </div>
        </form>

        <div class="links">
            <p>Already have an account? <a href="/login">Login</a></p>
        </div>
    </div>
</body>
</html>
"""

resume_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Resume - CareerSync AI</title>
    <style>
        /* Include all the existing styles from job_seeker_dashboard */
        
        .resume-container {
            max-width: 800px;
            margin: 30px auto;
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .resume-section {
            margin-bottom: 30px;
            animation: fadeIn 0.5s ease-out;
        }
        
        .resume-section h3 {
            color: #00d4ff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
        }
        
        .edit-section {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            margin-top: 15px;
        }
        
        .skill-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
        }
        
        .skill-input {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff;
            padding: 10px;
            border-radius: 5px;
            width: 100%;
            margin-top: 10px;
        }
        
        .add-button {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            border: none;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            margin-top: 10px;
            font-size: 0.9rem;
        }
        
        .add-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .remove-button {
            background: rgba(220, 53, 69, 0.8);
            color: #fff;
            border: none;
            padding: 2px 8px;
            border-radius: 12px;
            cursor: pointer;
            margin-left: 5px;
            font-size: 0.8rem;
        }
        
        .success-message {
            background: rgba(40, 167, 69, 0.2);
            color: #75ff75;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #75ff75;
        }
        
        .resume-preview {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-logo">
                <h2>CareerSync AI</h2>
            </div>
            <ul class="sidebar-menu">
                <li><a href="{{ url_for('job_seeker_dashboard_route') }}"><i class="fas fa-home"></i> Dashboard</a></li>
                <li><a href="/jobs"><i class="fas fa-briefcase"></i> Browse Jobs</a></li>
                <li><a href="/applications"><i class="fas fa-file-alt"></i> My Applications</a></li>
                <li><a href="/resume" class="active"><i class="fas fa-file-upload"></i> Resume</a></li>
                <li><a href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
            </ul>
        </div>
        
        <div class="main-content">
            <div class="header">
                <h1>My Resume</h1>
            </div>
            
            {% if message %}
            <div class="success-message">
                {{ message }}
            </div>
            {% endif %}
            
            <div class="resume-container">
                <form action="/resume" method="post" id="resumeForm">
                    <div class="resume-section">
                        <h3>Skills</h3>
                        <div class="skill-tags" id="skillTags">
                            {% for skill in resume.skills %}
                            <span class="skill-tag">
                                {{ skill }}
                                <button type="button" class="remove-button" onclick="removeSkill(this)">×</button>
                            </span>
                            {% endfor %}
                        </div>
                        <div class="edit-section">
                            <input type="text" id="newSkill" placeholder="Enter a new skill" class="skill-input">
                            <button type="button" class="add-button" onclick="addSkill()">Add Skill</button>
                            <input type="hidden" name="skills" id="skillsInput" value="{{ resume.skills|join(',') }}">
                        </div>
                    </div>
                    
                    <div class="resume-section">
                        <h3>Education</h3>
                        <div class="edit-section">
                            <textarea name="education" class="skill-input" rows="4" placeholder="Enter your education history">{{ resume.education|join('\n') }}</textarea>
                        </div>
                    </div>
                    
                    <div class="resume-section">
                        <h3>Experience</h3>
                        <div class="edit-section">
                            <textarea name="experience" class="skill-input" rows="6" placeholder="Enter your work experience">{{ resume.experience }}</textarea>
                        </div>
                    </div>
                    
                    <div class="resume-section">
                        <h3>Certifications</h3>
                        <div class="skill-tags" id="certTags">
                            {% for cert in resume.certifications %}
                            <span class="skill-tag">
                                {{ cert }}
                                <button type="button" class="remove-button" onclick="removeCert(this)">×</button>
                            </span>
                            {% endfor %}
                        </div>
                        <div class="edit-section">
                            <input type="text" id="newCert" placeholder="Enter a new certification" class="skill-input">
                            <button type="button" class="add-button" onclick="addCert()">Add Certification</button>
                            <input type="hidden" name="certifications" id="certsInput" value="{{ resume.certifications|join(',') }}">
                        </div>
                    </div>
                    
                    <div class="resume-section">
                        <h3>Resume Text</h3>
                        <div class="resume-preview">
                            {{ resume.resume_text }}
                        </div>
                    </div>
                    
                    <button type="submit" class="btn" style="margin-top: 20px;">Save Changes</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        function addSkill() {
            const input = document.getElementById('newSkill');
            const skill = input.value.trim();
            if (skill) {
                const skillTags = document.getElementById('skillTags');
                const span = document.createElement('span');
                span.className = 'skill-tag';
                span.innerHTML = `${skill}<button type="button" class="remove-button" onclick="removeSkill(this)">×</button>`;
                skillTags.appendChild(span);
                input.value = '';
                updateSkillsInput();
            }
        }
        
        function removeSkill(button) {
            button.parentElement.remove();
            updateSkillsInput();
        }
        
        function updateSkillsInput() {
            const skills = Array.from(document.getElementById('skillTags').children)
                .map(span => span.childNodes[0].textContent.trim());
            document.getElementById('skillsInput').value = skills.join(',');
        }
        
        function addCert() {
            const input = document.getElementById('newCert');
            const cert = input.value.trim();
            if (cert) {
                const certTags = document.getElementById('certTags');
                const span = document.createElement('span');
                span.className = 'skill-tag';
                span.innerHTML = `${cert}<button type="button" class="remove-button" onclick="removeCert(this)">×</button>`;
                certTags.appendChild(span);
                input.value = '';
                updateCertsInput();
            }
        }
        
        function removeCert(button) {
            button.parentElement.remove();
            updateCertsInput();
        }
        
        function updateCertsInput() {
            const certs = Array.from(document.getElementById('certTags').children)
                .map(span => span.childNodes[0].textContent.trim());
            document.getElementById('certsInput').value = certs.join(',');
        }
    </script>
    
    <!-- Font Awesome for icons -->
    <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
</body>
</html>
"""

resume_view_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Resume - CareerSync AI</title>
    <style>
        /* Include existing styles */
        .resume-container {
            max-width: 900px;
            margin: 30px auto;
            padding: 30px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }
        
        .section-title {
            color: #00d4ff;
            margin-bottom: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
        }
        
        .skill-tag {
            display: inline-block;
            background: rgba(0, 212, 255, 0.2);
            padding: 5px 15px;
            border-radius: 20px;
            margin: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .skill-tag:hover {
            background: rgba(0, 212, 255, 0.4);
        }
        
        .skill-input {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            width: 100%;
        }
        
        .btn-add {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            border: none;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            margin: 5px;
        }
        
        .btn-add:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .resume-text {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            white-space: pre-wrap;
            margin-top: 20px;
        }
        
        .edit-controls {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        
        textarea {
            width: 100%;
            min-height: 100px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <!-- Include your existing sidebar code -->
        </div>
        
        <div class="main-content">
            <div class="header">
                <h1>My Resume</h1>
            </div>
            
            <div class="resume-container">
                <form action="/resume/update" method="post" id="resumeForm">
                    <div class="section">
                        <h3 class="section-title">Skills</h3>
                        <div id="skillTags">
                            {% for skill in resume.skills %}
                            <span class="skill-tag">
                                {{ skill }}
                                <input type="hidden" name="skills[]" value="{{ skill }}">
                                <button type="button" onclick="removeTag(this)" class="btn-remove">×</button>
                            </span>
                            {% endfor %}
                        </div>
                        <div class="edit-controls">
                            <input type="text" id="newSkill" class="skill-input" placeholder="Add a new skill">
                            <button type="button" class="btn-add" onclick="addSkill()">Add Skill</button>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3 class="section-title">Certifications</h3>
                        <div id="certTags">
                            {% for cert in resume.certifications %}
                            <span class="skill-tag">
                                {{ cert }}
                                <input type="hidden" name="certifications[]" value="{{ cert }}">
                                <button type="button" onclick="removeTag(this)" class="btn-remove">×</button>
                            </span>
                            {% endfor %}
                        </div>
                        <div class="edit-controls">
                            <input type="text" id="newCert" class="skill-input" placeholder="Add a new certification">
                            <button type="button" class="btn-add" onclick="addCertification()">Add Certification</button>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3 class="section-title">Education</h3>
                        <textarea name="education" placeholder="Enter your education details">{{ resume.education|join('\n') }}</textarea>
                    </div>
                    
                    <div class="section">
                        <h3 class="section-title">Experience</h3>
                        <textarea name="experience" placeholder="Enter your work experience">{{ resume.experience }}</textarea>
                    </div>
                    
                    <div class="section">
                        <h3 class="section-title">Uploaded Resume</h3>
                        <div class="resume-text">{{ resume.resume_text }}</div>
                    </div>
                    
                    <button type="submit" class="btn-add" style="width: 100%; margin-top: 20px;">Save Changes</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        function addSkill() {
            const input = document.getElementById('newSkill');
            const skill = input.value.trim();
            if (skill) {
                addTag('skillTags', skill, 'skills[]');
                input.value = '';
            }
        }
        
        function addCertification() {
            const input = document.getElementById('newCert');
            const cert = input.value.trim();
            if (cert) {
                addTag('certTags', cert, 'certifications[]');
                input.value = '';
            }
        }
        
        function addTag(containerId, value, inputName) {
            const container = document.getElementById(containerId);
            const span = document.createElement('span');
            span.className = 'skill-tag';
            span.innerHTML = `
                ${value}
                <input type="hidden" name="${inputName}" value="${value}">
                <button type="button" onclick="removeTag(this)" class="btn-remove">×</button>
            `;
            container.appendChild(span);
        }
        
        function removeTag(button) {
            button.parentElement.remove();
        }
    </script>
</body>
</html>
"""

edit_job_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edit Job - CareerSync AI</title>
    <style>
        /* Include your existing styles */
        .edit-form {
            max-width: 800px;
            margin: 30px auto;
            padding: 30px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #fff;
            font-size: 1rem;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            color: #fff;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .form-control:focus {
            border-color: #00d4ff;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
        }
        
        textarea.form-control {
            min-height: 120px;
            resize: vertical;
        }
        
        .btn-group {
            display: flex;
            gap: 15px;
            margin-top: 30px;
        }
        
        .btn {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 30px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .flash-message {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            animation: slideIn 0.3s ease-out;
        }
        
        .flash-success {
            background: rgba(40, 167, 69, 0.2);
            border-left: 4px solid #28a745;
            color: #75ff75;
        }
        
        .flash-error {
            background: rgba(220, 53, 69, 0.2);
            border-left: 4px solid #dc3545;
            color: #ff6b6b;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideIn {
            from { transform: translateX(-100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-logo">
                <h2>CareerSync AI</h2>
            </div>
            <ul class="sidebar-menu">
                <li><a href="{{ url_for('recruiter_dashboard_route') }}"><i class="fas fa-home"></i> Dashboard</a></li>
                <li><a href="/post-job"><i class="fas fa-plus-circle"></i> Post Job</a></li>
                <li><a href="/applicants"><i class="fas fa-users"></i> Applicants</a></li>
                <li><a href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
            </ul>
        </div>
        
        <div class="main-content">
            <div class="header">
                <h1>Edit Job Listing</h1>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ category }}">
                            {{ message }}
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="edit-form">
                <form action="{{ url_for('edit_job', job_id=job[0]) }}" method="post">
                    <div class="form-group">
                        <label>Company Name</label>
                        <input type="text" name="company_name" class="form-control" value="{{ job[1] }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Role Name</label>
                        <input type="text" name="role_name" class="form-control" value="{{ job[2] }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Description</label>
                        <textarea name="description" class="form-control" required>{{ job[3] }}</textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Qualifications</label>
                        <textarea name="qualifications" class="form-control" required>{{ job[4] }}</textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Experience Required</label>
                        <input type="text" name="experience" class="form-control" value="{{ job[5] }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Location</label>
                        <input type="text" name="location" class="form-control" value="{{ job[6] }}" required>
                    </div>
                    
                    <div class="btn-group">
                        <button type="submit" class="btn btn-primary">Save Changes</button>
                        <a href="{{ url_for('recruiter_dashboard_route') }}" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <!-- Font Awesome for icons -->
    <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
</body>
</html>
"""

view_applicants_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Applicants - CareerSync AI</title>
    <style>
        /* Include your existing styles */
        .applicants-container {
            max-width: 1000px;
            margin: 30px auto;
            padding: 20px;
        }
        
        .applicant-card {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.3s ease;
        }
        
        .applicant-card:hover {
            transform: translateY(-5px);
        }
        
        .applicant-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .match-percentage {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #000;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }
        
        .skill-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 10px 0;
        }
        
        .skill-tag {
            background: rgba(0, 212, 255, 0.2);
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9em;
        }
        
        .status-badge {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .status-pending {
            background: #ffc107;
            color: #000;
        }
        
        .status-accepted {
            background: #28a745;
            color: #fff;
        }
        
        .status-rejected {
            background: #dc3545;
            color: #fff;
        }
        
        .action-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <!-- Include your sidebar here -->
        </div>
        
        <div class="main-content">
            <div class="header">
                <h1>Job Applicants</h1>
            </div>
            
            <div class="applicants-container">
                {% if applicants %}
                    {% for applicant in applicants %}
                    <div class="applicant-card">
                        <div class="applicant-header">
                            <h3>{{ applicant.username }}</h3>
                            <span class="match-percentage">{{ applicant.match_percentage }}% Match</span>
                        </div>
                        
                        <div class="skill-tags">
                            {% for skill in applicant.skills %}
                            <span class="skill-tag">{{ skill }}</span>
                            {% endfor %}
                        </div>
                        
                        <p><strong>Education:</strong> {{ applicant.education|join(', ') or 'Not specified' }}</p>
                        <p><strong>Experience:</strong> {{ applicant.experience }}</p>
                        <p><strong>Applied:</strong> {{ applicant.application_date }}</p>
                        
                        <div class="status-section">
                            <span class="status-badge status-{{ applicant.status }}">
                                {{ applicant.status|title }}
                            </span>
                        </div>
                        
                        <div class="action-buttons">
                            {% if applicant.status == 'pending' %}
                            <form action="{{ url_for('update_application_status', application_id=applicant.application_id) }}" method="post" style="display: inline;">
                                <input type="hidden" name="status" value="accepted">
                                <button type="submit" class="btn" style="background: #28a745;">Accept</button>
                            </form>
                            <form action="{{ url_for('update_application_status', application_id=applicant.application_id) }}" method="post" style="display: inline;">
                                <input type="hidden" name="status" value="rejected">
                                <button type="submit" class="btn" style="background: #dc3545;">Reject</button>
                            </form>
                            {% endif %}
                            <button class="btn" onclick="viewResume('{{ applicant.username }}')">View Resume</button>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No applicants yet for this position.</p>
                {% endif %}
            </div>
        </div>
    </div>
    
    <script>
        function viewResume(username) {
            // Implement resume viewing functionality
            alert('Viewing resume for ' + username);
        }
    </script>
</body>
</html>
"""

# Routes
@app.route('/')
def home():
    return render_template_string(home_page)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username
            session['role'] = user[3]  # role is stored in the 4th column

            if session['role'] == 'seeker':
                return redirect(url_for('job_seeker_dashboard_route'))
            else:
                return redirect(url_for('recruiter_dashboard_route'))
        else:
            return render_template_string(login_page, error='Invalid username or password')

    return render_template_string(login_page)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
            conn.commit()
            conn.close()

            return render_template_string(login_page, success='Registration successful! Please login.')
        except sqlite3.IntegrityError:
            conn.close()
            return render_template_string(register_page, error='Username already exists')

    type = request.args.get('type', '')
    return render_template_string(register_page, type=type)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/job_seeker_dashboard')
def job_seeker_dashboard_route():
    if 'username' not in session or session['role'] != 'seeker':
        return redirect(url_for('login'))

    # Get user ID
    user_id = get_user_id(session['username'])

    # Get resume data
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM resumes WHERE user_id = ?', (user_id,))
    resume = cursor.fetchone()

    # Get application counts
    cursor.execute('SELECT COUNT(*) FROM applications WHERE user_id = ? AND status = "pending"', (user_id,))
    pending_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM applications WHERE user_id = ? AND status = "accepted"', (user_id,))
    accepted_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM applications WHERE user_id = ? AND status = "rejected"', (user_id,))
    rejected_count = cursor.fetchone()[0]

    # Get jobs
    cursor.execute('''
    SELECT j.*, datetime(j.id, 'unixepoch') as posted_date
    FROM jobs j
    ORDER BY j.id DESC
    LIMIT 5
    ''')
    jobs = []
    for job in cursor.fetchall():
        job_dict = {
            'id': job[0],
            'company_name': job[1],
            'role_name': job[2],
            'description': job[3],
            'qualifications': job[4],
            'experience': job[5],
            'location': job[6],
            'posted_date': job[8],
            'match_percentage': 85  # Placeholder, would be calculated based on resume
        }
        jobs.append(job_dict)

    # Get skills, education, experience if resume exists
    skills = []
    education = []
    experience = "Not specified"

    if resume:
        skills = resume[3].split(',') if resume[3] else []
        education = resume[4].split(',') if resume[4] else []
        experience = resume[5] if resume[5] else "Not specified"

    conn.close()

    return render_template_string(
        job_seeker_dashboard,
        resume=resume,
        skills=skills,
        education=education,
        experience=experience,
        pending_count=pending_count,
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        jobs=jobs
    )

@app.route('/recruiter_dashboard')
def recruiter_dashboard_route():  # Make sure this matches what you use in url_for()
    if 'username' not in session or session['role'] != 'recruiter':
        return redirect(url_for('login'))

    # Get user ID
    user_id = get_user_id(session['username'])

    # Get job counts and applicant data
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Count active jobs
    cursor.execute('SELECT COUNT(*) FROM jobs WHERE posted_by = ?', (user_id,))
    active_jobs = cursor.fetchone()[0]

    # Count total applicants
    cursor.execute('''
    SELECT COUNT(*) FROM applications a
    JOIN jobs j ON a.job_id = j.id
    WHERE j.posted_by = ?
    ''', (user_id,))
    total_applicants = cursor.fetchone()[0]

    # Count pending reviews
    cursor.execute('''
    SELECT COUNT(*) FROM applications a
    JOIN jobs j ON a.job_id = j.id
    WHERE j.posted_by = ? AND a.status = "pending"
    ''', (user_id,))
    pending_reviews = cursor.fetchone()[0]

    # Get recent activities (placeholder data)
    recent_activities = [
        {'action': 'New application received for Software Engineer', 'time': '2 hours ago'},
        {'action': 'Candidate accepted for Data Scientist position', 'time': '1 day ago'},
        {'action': 'Posted new job: Frontend Developer', 'time': '3 days ago'},
    ]

    # Get jobs posted by this recruiter
    cursor.execute('''
    SELECT j.*, datetime(j.id, 'unixepoch') as posted_date,
           (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.id) as applicant_count
    FROM jobs j
    WHERE j.posted_by = ?
    ORDER BY j.id DESC
    ''', (user_id,))

    jobs = []
    for job in cursor.fetchall():
        job_dict = {
            'id': job[0],
            'company_name': job[1],
            'role_name': job[2],
            'description': job[3],
            'qualifications': job[4],
            'experience': job[5],
            'location': job[6],
            'posted_date': job[8],
            'applicant_count': job[9]
        }
        jobs.append(job_dict)

    # Get recent applicants (placeholder data)
    applicants = [
        {
            'id': 1,
            'username': 'john.doe@example.com',
            'job_title': 'Software Engineer',
            'skills': ['Python', 'JavaScript', 'React', 'Node.js'],
            'match_percentage': 92
        },
        {
            'id': 2,
            'username': 'jane.smith@example.com',
            'job_title': 'Data Scientist',
            'skills': ['Python', 'Machine Learning', 'SQL', 'TensorFlow'],
            'match_percentage': 88
        },
        {
            'id': 3,
            'username': 'mike.johnson@example.com',
            'job_title': 'Frontend Developer',
            'skills': ['HTML', 'CSS', 'JavaScript', 'React', 'Vue.js'],
            'match_percentage': 75
        }
    ]

    conn.close()

    return render_template_string(
        recruiter_dashboard,
        active_jobs=active_jobs,
        total_applicants=total_applicants,
        pending_reviews=pending_reviews,
        recent_activities=recent_activities,
        jobs=jobs,
        applicants=applicants
    )

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'username' not in session or session['role'] != 'seeker':
        return redirect(url_for('login'))

    if 'resume' not in request.files:
        return redirect(url_for('job_seeker_dashboard_route'))

    file = request.files['resume']

    if file.filename == '':
        return redirect(url_for('job_seeker_dashboard_route'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Analyze resume
        analysis = analyze_resume(filepath)

        # Store in database
        user_id = get_user_id(session['username'])

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Check if resume already exists
        cursor.execute('SELECT id FROM resumes WHERE user_id = ?', (user_id,))
        existing_resume = cursor.fetchone()

        if existing_resume:
            # Update existing resume
            cursor.execute('''
            UPDATE resumes
            SET resume_text = ?, skills = ?, education = ?, experience = ?
            WHERE user_id = ?
            ''', (
                analysis['full_text'],
                ','.join(analysis['skills']),
                ','.join(analysis['education']),
                analysis['experience'],
                user_id
            ))
        else:
            # Insert new resume
            cursor.execute('''
            INSERT INTO resumes (user_id, resume_text, skills, education, experience)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                analysis['full_text'],
                ','.join(analysis['skills']),
                ','.join(analysis['education']),
                analysis['experience']
            ))

        conn.commit()
        conn.close()

        return redirect(url_for('job_seeker_dashboard_route'))

    return redirect(url_for('job_seeker_dashboard_route'))

@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'username' not in session or session['role'] != 'recruiter':
        return redirect(url_for('login'))

    if request.method == 'POST':
        company_name = request.form.get('company_name')
        role_name = request.form.get('role_name')
        job_type = request.form.get('job_type')
        location = request.form.get('location')
        experience = request.form.get('experience')
        description = request.form.get('description')
        qualifications = request.form.get('qualifications')
        
        user_id = get_user_id(session['username'])
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO jobs (company_name, role_name, job_type, description, qualifications, 
                                experience, location, posted_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (company_name, role_name, job_type, description, qualifications, 
                  experience, location, user_id))
            
            conn.commit()
            flash('Job posted successfully!', 'success')
        except sqlite3.Error as e:
            flash(f'Error posting job: {str(e)}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('recruiter_dashboard_route'))

    # For GET requests, render the form
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Post a New Job</title>
        <style>
            .container {
                max-width: 800px;
                margin: 30px auto;
                padding: 20px;
                background: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .form-group {
                margin-bottom: 1rem;
            }
            .form-control {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
                margin-top: 5px;
            }
            label {
                font-weight: bold;
                display: block;
                margin-bottom: 5px;
            }
            .btn-primary {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            .btn-primary:hover {
                background-color: #0056b3;
            }
            .btn-secondary {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-right: 10px;
            }
            .btn-secondary:hover {
                background-color: #545b62;
            }
            .buttons {
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Post a New Job</h2>
            <form action="{{ url_for('post_job') }}" method="post">
                <div class="form-group">
                    <label>Company Name:</label>
                    <input type="text" class="form-control" name="company_name" required>
                </div>
                
                <div class="form-group">
                    <label>Role Name:</label>
                    <input type="text" class="form-control" name="role_name" required>
                </div>
                
                <div class="form-group">
                    <label>Job Type:</label>
                    <select class="form-control" name="job_type" required>
                        <option value="">Select Job Type</option>
                        <option value="Full Time">Full Time</option>
                        <option value="Part Time">Part Time</option>
                        <option value="Internship">Internship</option>
                        <option value="Contract">Contract</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Location:</label>
                    <select class="form-control" name="location" required>
                        <option value="">Select Location</option>
                        <option value="Mumbai">Mumbai</option>
                        <option value="Delhi">Delhi</option>
                        <option value="Bangalore">Bangalore</option>
                        <option value="Hyderabad">Hyderabad</option>
                        <option value="Chennai">Chennai</option>
                        <option value="Kolkata">Kolkata</option>
                        <option value="Pune">Pune</option>
                        <option value="Ahmedabad">Ahmedabad</option>
                        <option value="Remote">Remote</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Experience Required:</label>
                    <select class="form-control" name="experience" required>
                        <option value="">Select Experience</option>
                        <option value="Fresher">Fresher</option>
                        <option value="1 year">1 Year</option>
                        <option value="2 years">2 Years</option>
                        <option value="3 years">3 Years</option>
                        <option value="4 years">4 Years</option>
                        <option value="5+ years">5+ Years</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Job Description:</label>
                    <textarea class="form-control" name="description" rows="4" required></textarea>
                </div>
                
                <div class="form-group">
                    <label>Qualifications Required:</label>
                    <textarea class="form-control" name="qualifications" rows="4" required></textarea>
                </div>
                
                <div class="buttons">
                    <a href="{{ url_for('recruiter_dashboard_route') }}" class="btn-secondary">Cancel</a>
                    <button type="submit" class="btn-primary">Post Job</button>
                </div>
            </form>
        </div>
    </body>
    </html>
    """)

@app.route('/apply/<int:job_id>')
def apply_for_job(job_id):
    if 'username' not in session or session['role'] != 'seeker':
        return redirect(url_for('login'))

    user_id = get_user_id(session['username'])

    # Check if already applied
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM applications WHERE job_id = ? AND user_id = ?', (job_id, user_id))
    existing_application = cursor.fetchone()

    if existing_application:
        conn.close()
        return redirect(url_for('job_seeker_dashboard_route'))

    # Get resume text
    cursor.execute('SELECT resume_text FROM resumes WHERE user_id = ?', (user_id,))
    resume = cursor.fetchone()

    if not resume:
        conn.close()
        return redirect(url_for('job_seeker_dashboard_route'))

    resume_text = resume[0]

    # Get job description
    cursor.execute('SELECT description, qualifications, experience FROM jobs WHERE id = ?', (job_id,))
    job = cursor.fetchone()

    if not job:
        conn.close()
        return redirect(url_for('job_seeker_dashboard_route'))

    job_text = job[0] + " " + job[1] + " " + job[2]

    # Calculate match percentage
    match_percentage = calculate_match_percentage(resume_text, job_text)

    # Create application
    cursor.execute('''
    INSERT INTO applications (job_id, user_id, match_percentage, status, application_date)
    VALUES (?, ?, ?, ?, datetime('now'))
    ''', (job_id, user_id, match_percentage, 'pending'))

    conn.commit()
    conn.close()

    return redirect(url_for('job_seeker_dashboard_route'))

@app.route('/jobs')
def browse_jobs():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get all jobs
    cursor.execute('SELECT * FROM jobs ORDER BY posted_date DESC')
    jobs_data = cursor.fetchall()
    
    jobs_with_match = []
    
    for job in jobs_data:
        # Generate a random match percentage between 55 and 98
        match_percent = calculate_match_percentage(None, None)
        
        job_dict = {
            'id': job[0],
            'company_name': job[1],
            'role_name': job[2],
            'description': job[3],
            'qualifications': job[4],
            'experience': job[5],
            'location': job[6],
            'posted_date': job[7] if len(job) > 7 else datetime.now().strftime('%Y-%m-%d'),
            'match_percentage': match_percent
        }
        jobs_with_match.append(job_dict)
    
    conn.close()
    return render_template('browse_jobs.html', jobs=jobs_with_match)

@app.route('/job/<int:job_id>')
def view_job_details(job_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get job details
    cursor.execute('''
        SELECT j.*, u.username as posted_by_user
        FROM jobs j
        LEFT JOIN users u ON j.posted_by = u.id
        WHERE j.id = ?
    ''', (job_id,))
    
    job_data = cursor.fetchone()
    
    if not job_data:
        conn.close()
        return redirect(url_for('browse_jobs'))
    
    # Get user's resume match percentage if exists
    match_percentage = None
    if session.get('role') == 'seeker':
        user_id = get_user_id(session['username'])
        cursor.execute('SELECT resume_text FROM resumes WHERE user_id = ?', (user_id,))
        resume = cursor.fetchone()
        if resume:
            match_percentage = calculate_match_percentage(resume[0], job_data[3])  # Compare resume text with job description
    
    # Check if user has already applied
    has_applied = False
    if session.get('role') == 'seeker':
        user_id = get_user_id(session['username'])
        cursor.execute('SELECT id FROM applications WHERE job_id = ? AND user_id = ?', (job_id, user_id))
        has_applied = cursor.fetchone() is not None
    
    job = {
        'id': job_data[0],
        'company_name': job_data[1],
        'role_name': job_data[2],
        'description': job_data[3],
        'qualifications': job_data[4],
        'experience': job_data[5],
        'location': job_data[6],
        'posted_date': job_data[7] if len(job_data) > 7 else datetime.now().strftime('%Y-%m-%d'),
        'posted_by': job_data[8] if len(job_data) > 8 else None,
        'match_percentage': match_percentage,
        'has_applied': has_applied
    }
    
    conn.close()
    return render_template('job_details.html', job=job)

@app.route('/applications')
def view_applications():
    if 'username' not in session or session['role'] != 'seeker':
        return redirect(url_for('login'))

    user_id = get_user_id(session['username'])

    # Get all applications
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT a.*, j.company_name, j.role_name, j.location
    FROM applications a
    JOIN jobs j ON a.job_id = j.id
    WHERE a.user_id = ?
    ORDER BY a.application_date DESC
    ''', (user_id,))

    applications = []
    for app in cursor.fetchall():
        app_dict = {
            'id': app[0],
            'job_id': app[1],
            'match_percentage': app[3],
            'status': app[4],
            'application_date': app[5],
            'company_name': app[6],
            'role_name': app[7],
            'location': app[8]
        }
        applications.append(app_dict)
    conn.close()
    return render_template_string(job_seeker_dashboard, applications=applications)

@app.route('/resume')
def resume():
    if 'username' not in session or session['role'] != 'seeker':
        return redirect(url_for('login'))

    user_id = get_user_id(session['username'])
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get resume data
    cursor.execute('SELECT * FROM resumes WHERE user_id = ?', (user_id,))
    resume_data = cursor.fetchone()
    
    if resume_data:
        resume = {
            'id': resume_data[0],
            'user_id': resume_data[1],
            'resume_text': resume_data[2],
            'skills': resume_data[3].split(',') if resume_data[3] else [],
            'education': resume_data[4].split(',') if resume_data[4] else [],
            'experience': resume_data[5] if resume_data[5] else '',
            'certifications': resume_data[6].split(',') if len(resume_data) > 6 and resume_data[6] else []
        }
    else:
        resume = {
            'skills': [],
            'education': [],
            'experience': '',
            'certifications': [],
            'resume_text': ''
        }
    
    conn.close()
    return render_template('resume.html', resume=resume)

@app.route('/resume/update', methods=['POST'])
def update_resume():
    if 'username' not in session or session['role'] != 'seeker':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    user_id = get_user_id(session['username'])
    
    # Get form data
    skills = request.form.get('skills', '').split(',')
    education = request.form.get('education', '')
    experience = request.form.get('experience', '')
    certifications = request.form.get('certifications', '').split(',')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Check if resume exists
    cursor.execute('SELECT id FROM resumes WHERE user_id = ?', (user_id,))
    resume_exists = cursor.fetchone()
    
    if resume_exists:
        # Update existing resume
        cursor.execute('''
            UPDATE resumes 
            SET skills = ?, education = ?, experience = ?, certifications = ?
            WHERE user_id = ?
        ''', (
            ','.join(filter(None, skills)),
            education,
            experience,
            ','.join(filter(None, certifications)),
            user_id
        ))
    else:
        # Insert new resume
        cursor.execute('''
            INSERT INTO resumes (user_id, skills, education, experience, certifications)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            ','.join(filter(None, skills)),
            education,
            experience,
            ','.join(filter(None, certifications))
        ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Resume updated successfully'})

@app.route('/resume/update-skills', methods=['POST'])
def update_resume_skills():
    if 'username' not in session or session['role'] != 'seeker':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    user_id = get_user_id(session['username'])
    data = request.get_json()
    
    if not data or 'skills' not in data:
        return jsonify({'success': False, 'message': 'No skills provided'})
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE resumes SET skills = ? WHERE user_id = ?',
                  (','.join(data['skills']), user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Skills updated successfully'})

@app.route('/resume/update-education', methods=['POST'])
def update_resume_education():
    if 'username' not in session or session['role'] != 'seeker':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    user_id = get_user_id(session['username'])
    data = request.get_json()
    
    if not data or 'education' not in data:
        return jsonify({'success': False, 'message': 'No education provided'})
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE resumes SET education = ? WHERE user_id = ?',
                  (data['education'], user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Education updated successfully'})

@app.route('/resume/update-experience', methods=['POST'])
def update_resume_experience():
    if 'username' not in session or session['role'] != 'seeker':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    user_id = get_user_id(session['username'])
    data = request.get_json()
    
    if not data or 'experience' not in data:
        return jsonify({'success': False, 'message': 'No experience provided'})
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE resumes SET experience = ? WHERE user_id = ?',
                  (data['experience'], user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Experience updated successfully'})

@app.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):  # Add job_id parameter here
    if 'username' not in session or session['role'] != 'recruiter':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get the current user's ID
    user_id = get_user_id(session['username'])
    
    try:
        # First verify that this job belongs to the logged-in recruiter
        cursor.execute('SELECT * FROM jobs WHERE id = ? AND posted_by = ?', (job_id, user_id))
        job = cursor.fetchone()
        
        if not job:
            flash('Job not found or you do not have permission to edit it.', 'error')
            return redirect(url_for('recruiter_dashboard_route'))
        
        if request.method == 'POST':
            # Update job details
            company_name = request.form.get('company_name')
            role_name = request.form.get('role_name')
            job_type = request.form.get('job_type')
            location = request.form.get('location')
            experience = request.form.get('experience')
            description = request.form.get('description')
            qualifications = request.form.get('qualifications')
            
            cursor.execute('''
                UPDATE jobs 
                SET company_name = ?, role_name = ?, job_type = ?, 
                    description = ?, qualifications = ?, experience = ?, 
                    location = ?
                WHERE id = ? AND posted_by = ?
            ''', (company_name, role_name, job_type, description, 
                  qualifications, experience, location, job_id, user_id))
            
            conn.commit()
            flash('Job updated successfully!', 'success')
            return redirect(url_for('recruiter_dashboard_route'))
        
        # For GET request, show the edit form with current values
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Edit Job</title>
            <style>
                .container {
                    max-width: 800px;
                    margin: 30px auto;
                    padding: 20px;
                    background: #fff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .form-group {
                    margin-bottom: 1rem;
                }
                .form-control {
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                    margin-top: 5px;
                }
                label {
                    font-weight: bold;
                    display: block;
                    margin-bottom: 5px;
                }
                .btn-primary {
                    background-color: #007bff;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .btn-primary:hover {
                    background-color: #0056b3;
                }
                .btn-secondary {
                    background-color: #6c757d;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    margin-right: 10px;
                }
                .btn-secondary:hover {
                    background-color: #545b62;
                }
                .buttons {
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Edit Job</h2>
                <form action="{{ url_for('edit_job', job_id=job[0]) }}" method="post">
                    <div class="form-group">
                        <label>Company Name:</label>
                        <input type="text" class="form-control" name="company_name" value="{{ job[1] }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Role Name:</label>
                        <input type="text" class="form-control" name="role_name" value="{{ job[2] }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Job Type:</label>
                        <select class="form-control" name="job_type" required>
                            <option value="Full Time" {{ 'selected' if job[3] == 'Full Time' }}>Full Time</option>
                            <option value="Part Time" {{ 'selected' if job[3] == 'Part Time' }}>Part Time</option>
                            <option value="Internship" {{ 'selected' if job[3] == 'Internship' }}>Internship</option>
                            <option value="Contract" {{ 'selected' if job[3] == 'Contract' }}>Contract</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Location:</label>
                        <select class="form-control" name="location" required>
                            <option value="Mumbai" {{ 'selected' if job[7] == 'Mumbai' }}>Mumbai</option>
                            <option value="Delhi" {{ 'selected' if job[7] == 'Delhi' }}>Delhi</option>
                            <option value="Bangalore" {{ 'selected' if job[7] == 'Bangalore' }}>Bangalore</option>
                            <option value="Hyderabad" {{ 'selected' if job[7] == 'Hyderabad' }}>Hyderabad</option>
                            <option value="Chennai" {{ 'selected' if job[7] == 'Chennai' }}>Chennai</option>
                            <option value="Kolkata" {{ 'selected' if job[7] == 'Kolkata' }}>Kolkata</option>
                            <option value="Pune" {{ 'selected' if job[7] == 'Pune' }}>Pune</option>
                            <option value="Ahmedabad" {{ 'selected' if job[7] == 'Ahmedabad' }}>Ahmedabad</option>
                            <option value="Remote" {{ 'selected' if job[7] == 'Remote' }}>Remote</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Experience Required:</label>
                        <select class="form-control" name="experience" required>
                            <option value="Fresher" {{ 'selected' if job[6] == 'Fresher' }}>Fresher</option>
                            <option value="1 year" {{ 'selected' if job[6] == '1 year' }}>1 Year</option>
                            <option value="2 years" {{ 'selected' if job[6] == '2 years' }}>2 Years</option>
                            <option value="3 years" {{ 'selected' if job[6] == '3 years' }}>3 Years</option>
                            <option value="4 years" {{ 'selected' if job[6] == '4 years' }}>4 Years</option>
                            <option value="5+ years" {{ 'selected' if job[6] == '5+ years' }}>5+ Years</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Job Description:</label>
                        <textarea class="form-control" name="description" rows="4" required>{{ job[4] }}</textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Qualifications Required:</label>
                        <textarea class="form-control" name="qualifications" rows="4" required>{{ job[5] }}</textarea>
                    </div>
                    
                    <div class="buttons">
                        <a href="{{ url_for('recruiter_dashboard_route') }}" class="btn-secondary">Cancel</a>
                        <button type="submit" class="btn-primary">Save Changes</button>
                    </div>
                </form>
            </div>
        </body>
        </html>
        """, job=job)
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('recruiter_dashboard_route'))
    finally:
        conn.close()

@app.route('/view-applicants/<int:job_id>')
def view_applicants(job_id):
    if 'username' not in session or session['role'] != 'recruiter':
        return redirect(url_for('login'))
        
    user_id = get_user_id(session['username'])
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get job details and verify ownership
    cursor.execute('''
        SELECT role_name, company_name, location 
        FROM jobs 
        WHERE id = ? AND posted_by = ?
    ''', (job_id, user_id))
    
    job = cursor.fetchone()
    if not job:
        conn.close()
        return redirect(url_for('recruiter_dashboard_route'))
    
    # Get all applicants for this job
    cursor.execute('''
        SELECT 
            u.username,
            a.match_percentage,
            a.status,
            a.application_date,
            r.skills,
            r.education,
            r.experience,
            a.id as application_id
        FROM applications a
        JOIN users u ON a.user_id = u.id
        LEFT JOIN resumes r ON u.id = r.user_id
        WHERE a.job_id = ?
        ORDER BY a.match_percentage DESC
    ''', (job_id,))
    
    applicants = []
    for row in cursor.fetchall():
        applicant = {
            'username': row[0],
            'match_percentage': row[1],
            'status': row[2],
            'application_date': row[3],
            'skills': row[4].split(',') if row[4] else [],
            'education': row[5].split(',') if row[5] else [],
            'experience': row[6] if row[6] else "Not specified",
            'application_id': row[7]
        }
        applicants.append(applicant)
    
    conn.close()
    return render_template_string(view_applicants_template, applicants=applicants, job_id=job_id)

@app.route('/update-application-status/<int:application_id>', methods=['POST'])
def update_application_status(application_id):
    if 'username' not in session or session['role'] != 'recruiter':
        return redirect(url_for('login'))
    
    status = request.form.get('status')
    if status not in ['accepted', 'rejected']:
        return redirect(url_for('recruiter_dashboard_route'))
    
    user_id = get_user_id(session['username'])
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get job_id and verify recruiter owns this job
    cursor.execute('''
        SELECT j.id 
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.id = ? AND j.posted_by = ?
    ''', (application_id, user_id))
    
    result = cursor.fetchone()
    if not result:
        conn.close()
        return redirect(url_for('recruiter_dashboard_route'))
    
    job_id = result[0]
    
    # Update application status
    cursor.execute('UPDATE applications SET status = ? WHERE id = ?', 
                  (status, application_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('view_applicants', job_id=job_id))

@app.route('/post-job-form')
def post_job_form():
    return render_template_string("""
    <div class="container mt-4">
        <h2>Post a New Job</h2>
        <form action="{{ url_for('post_job') }}" method="post">
            <div class="form-group">
                <label>Company Name:</label>
                <input type="text" class="form-control" name="company_name" required>
            </div>
            
            <div class="form-group">
                <label>Role Name:</label>
                <input type="text" class="form-control" name="role_name" required>
            </div>
            
            <div class="form-group">
                <label>Job Type:</label>
                <select class="form-control" name="job_type" required>
                    <option value="">Select Job Type</option>
                    <option value="Full Time">Full Time</option>
                    <option value="Part Time">Part Time</option>
                    <option value="Internship">Internship</option>
                    <option value="Contract">Contract</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Location:</label>
                <select class="form-control" name="location" required>
                    <option value="">Select Location</option>
                    <option value="Mumbai">Mumbai</option>
                    <option value="Delhi">Delhi</option>
                    <option value="Bangalore">Bangalore</option>
                    <option value="Hyderabad">Hyderabad</option>
                    <option value="Chennai">Chennai</option>
                    <option value="Kolkata">Kolkata</option>
                    <option value="Pune">Pune</option>
                    <option value="Ahmedabad">Ahmedabad</option>
                    <option value="Remote">Remote</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Experience Required:</label>
                <select class="form-control" name="experience" required>
                    <option value="">Select Experience</option>
                    <option value="Fresher">Fresher</option>
                    <option value="1 year">1 Year</option>
                    <option value="2 years">2 Years</option>
                    <option value="3 years">3 Years</option>
                    <option value="4 years">4 Years</option>
                    <option value="5+ years">5+ Years</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Job Description:</label>
                <textarea class="form-control" name="description" rows="4" required></textarea>
            </div>
            
            <div class="form-group">
                <label>Qualifications Required:</label>
                <textarea class="form-control" name="qualifications" rows="4" required></textarea>
            </div>
            
            <button type="submit" class="btn btn-primary">Post Job</button>
        </form>
    </div>
    
    <style>
    .form-group {
        margin-bottom: 1rem;
    }
    .form-control {
        width: 100%;
        padding: 0.375rem 0.75rem;
        border: 1px solid #ced4da;
        border-radius: 0.25rem;
    }
    select.form-control {
        height: calc(1.5em + 0.75rem + 2px);
    }
    .btn-primary {
        color: #fff;
        background-color: #007bff;
        border-color: #007bff;
        padding: 0.375rem 0.75rem;
        border-radius: 0.25rem;
        cursor: pointer;
    }
    .btn-primary:hover {
        background-color: #0069d9;
        border-color: #0062cc;
    }
    </style>
    """)

@app.route('/manage-jobs')
def manage_jobs():
    if 'username' not in session or session['role'] != 'recruiter':
        return redirect(url_for('login'))
    
    user_id = get_user_id(session['username'])
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get jobs posted by this recruiter
    cursor.execute('''
    SELECT j.*, datetime(j.id, 'unixepoch') as posted_date,
           (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.id) as applicant_count
    FROM jobs j
    WHERE j.posted_by = ?
    ORDER BY j.id DESC
    ''', (user_id,))
    
    jobs = []
    for job in cursor.fetchall():
        job_dict = {
            'id': job[0],
            'company_name': job[1],
            'role_name': job[2],
            'description': job[3],
            'qualifications': job[4],
            'experience': job[5],
            'location': job[6],
            'job_type': job[7] if len(job) > 7 else 'Full Time',
            'posted_date': job[8],
            'applicant_count': job[9]
        }
        jobs.append(job_dict)
    
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Manage Jobs - CareerSync AI</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
                color: #333;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }
            
            h1 {
                color: #1976D2;
                margin: 0;
            }
            
            .btn {
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            
            .btn-primary {
                background: #1976D2;
                color: white;
                border: none;
            }
            
            .btn-secondary {
                background: #E0E0E0;
                color: #333;
                border: none;
            }
            
            .job-list {
                display: grid;
                gap: 20px;
            }
            
            .job-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .job-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 15px;
            }
            
            .job-title {
                margin: 0;
                color: #1976D2;
                font-size: 1.4em;
            }
            
            .job-company {
                color: #666;
                margin: 5px 0;
            }
            
            .job-meta {
                display: flex;
                gap: 20px;
                margin: 15px 0;
                flex-wrap: wrap;
            }
            
            .meta-item {
                display: flex;
                align-items: center;
                gap: 5px;
                color: #666;
            }
            
            .actions {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            
            .applicant-count {
                background: #4CAF50;
                color: white;
                padding: 5px 15px;
                border-radius: 15px;
                font-weight: 500;
            }
            
            .search-bar {
                margin-bottom: 20px;
                display: flex;
                gap: 10px;
            }
            
            .search-bar input {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 1em;
            }
            
            .search-bar button {
                padding: 10px 20px;
                background: #1976D2;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            
            .back-link {
                color: #666;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 5px;
                margin-bottom: 20px;
            }
            
            .back-link:hover {
                color: #1976D2;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="{{ url_for('recruiter_dashboard_route') }}" class="back-link">
                <i class="fas fa-arrow-left"></i> Back to Dashboard
            </a>
            
            <div class="header">
                <h1>Manage Jobs</h1>
                <a href="{{ url_for('post_job') }}" class="btn btn-primary">Post New Job</a>
            </div>
            
            <div class="search-bar">
                <input type="text" placeholder="Search jobs..." id="searchInput">
                <button onclick="searchJobs()">Search</button>
            </div>
            
            <div class="job-list">
                {% if jobs %}
                    {% for job in jobs %}
                    <div class="job-card">
                        <div class="job-header">
                            <div>
                                <h2 class="job-title">{{ job.role_name }}</h2>
                                <div class="job-company">{{ job.company_name }}</div>
                            </div>
                            <div class="applicant-count">
                                {{ job.applicant_count }} Applicant{% if job.applicant_count != 1 %}s{% endif %}
                            </div>
                        </div>
                        
                        <div class="job-meta">
                            <div class="meta-item">
                                <i class="fas fa-map-marker-alt"></i>
                                {{ job.location }}
                            </div>
                            <div class="meta-item">
                                <i class="fas fa-briefcase"></i>
                                {{ job.job_type }}
                            </div>
                            <div class="meta-item">
                                <i class="fas fa-clock"></i>
                                {{ job.experience }}
                            </div>
                            <div class="meta-item">
                                <i class="fas fa-calendar"></i>
                                Posted on {{ job.posted_date }}
                            </div>
                        </div>
                        
                        <div class="actions">
                            <a href="{{ url_for('edit_job', job_id=job.id) }}" class="btn btn-secondary">Edit</a>
                            <a href="{{ url_for('view_applicants', job_id=job.id) }}" class="btn btn-primary">View Applicants</a>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No jobs posted yet. <a href="{{ url_for('post_job') }}">Post your first job</a></p>
                {% endif %}
            </div>
        </div>
        
        <!-- Font Awesome for icons -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        
        <script>
            function searchJobs() {
                const searchInput = document.getElementById('searchInput').value.toLowerCase();
                const jobCards = document.querySelectorAll('.job-card');
                
                jobCards.forEach(card => {
                    const title = card.querySelector('.job-title').textContent.toLowerCase();
                    const company = card.querySelector('.job-company').textContent.toLowerCase();
                    const location = card.querySelector('.meta-item:first-child').textContent.toLowerCase();
                    
                    if (title.includes(searchInput) || company.includes(searchInput) || location.includes(searchInput)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
        </script>
    </body>
    </html>
    ''', jobs=jobs)

@app.route('/view-all-applicants')
def view_all_applicants():
    if 'username' not in session or session['role'] != 'recruiter':
        return redirect(url_for('login'))
    
    user_id = get_user_id(session['username'])
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get all applicants for jobs posted by this recruiter
    cursor.execute('''
        SELECT 
            a.id as application_id,
            a.status,
            a.application_date,
            a.match_percentage,
            u.username,
            j.role_name,
            j.id as job_id,
            r.skills,
            r.education,
            r.experience
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN users u ON a.user_id = u.id
        LEFT JOIN resumes r ON u.id = r.user_id
        WHERE j.posted_by = ?
        ORDER BY a.application_date DESC
    ''', (user_id,))
    
    applications = []
    for row in cursor.fetchall():
        application = {
            'id': row[0],
            'status': row[1],
            'application_date': row[2],
            'match_percentage': row[3],
            'username': row[4],
            'job_title': row[5],
            'job_id': row[6],
            'skills': row[7].split(',') if row[7] else [],
            'education': row[8].split(',') if row[8] else [],
            'experience': row[9] if row[9] else "Not specified"
        }
        applications.append(application)
    
    # Get statistics
    cursor.execute('''
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
               SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.posted_by = ?
    ''', (user_id,))
    
    stats = cursor.fetchone()
    total_applicants = stats[0] or 0
    pending_count = stats[1] or 0
    accepted_count = stats[2] or 0
    rejected_count = stats[3] or 0
    
    conn.close()
    
    return render_template('applicants.html',
                         applicants=applications,
                         total_applicants=total_applicants,
                         pending_count=pending_count,
                         accepted_count=accepted_count,
                         rejected_count=rejected_count)

@app.route('/company-profile')
def company_profile():
    if 'username' not in session or session['role'] != 'recruiter':
        return redirect(url_for('login'))
    
    user_id = get_user_id(session['username'])
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get company profile data
    cursor.execute('''
        SELECT rp.*, 
               COUNT(DISTINCT j.id) as total_jobs,
               COUNT(DISTINCT a.id) as total_applicants
        FROM recruiter_profiles rp
        LEFT JOIN jobs j ON rp.user_id = j.posted_by
        LEFT JOIN applications a ON j.id = a.job_id
        WHERE rp.user_id = ?
        GROUP BY rp.user_id
    ''', (user_id,))
    
    profile = cursor.fetchone()
    
    if profile:
        profile_data = {
            'company_name': profile[1],
            'industry': profile[2],
            'location': profile[3],
            'website': profile[4] if len(profile) > 4 else None,
            'description': profile[5] if len(profile) > 5 else None,
            'total_jobs': profile[6],
            'total_applicants': profile[7]
        }
    else:
        profile_data = {
            'company_name': '',
            'industry': '',
            'location': '',
            'website': '',
            'description': '',
            'total_jobs': 0,
            'total_applicants': 0
        }
    
    conn.close()
    return render_template('company_profile.html', profile=profile_data)

@app.route('/analytics')
def analytics():
    if 'username' not in session or session['role'] != 'recruiter':
        return redirect(url_for('login'))
    
    user_id = get_user_id(session['username'])
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get total jobs posted
    cursor.execute('SELECT COUNT(*) FROM jobs WHERE posted_by = ?', (user_id,))
    total_jobs = cursor.fetchone()[0]
    
    # Get total applicants
    cursor.execute('''
        SELECT COUNT(*) 
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.posted_by = ?
    ''', (user_id,))
    total_applicants = cursor.fetchone()[0]
    
    # Get application status breakdown
    cursor.execute('''
        SELECT a.status, COUNT(*) as count
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.posted_by = ?
        GROUP BY a.status
    ''', (user_id,))
    status_counts = cursor.fetchall()
    
    # Calculate average match rate
    cursor.execute('''
        SELECT AVG(match_percentage)
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.posted_by = ?
    ''', (user_id,))
    avg_match = cursor.fetchone()[0] or 0
    
    # Get applications timeline (last 7 days)
    cursor.execute('''
        SELECT DATE(application_date) as date, COUNT(*) as count
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.posted_by = ?
        AND application_date >= date('now', '-7 days')
        GROUP BY DATE(application_date)
        ORDER BY date
    ''', (user_id,))
    timeline_data = cursor.fetchall()
    
    # Get top companies by applicants
    cursor.execute('''
        SELECT j.company_name, COUNT(*) as applicant_count
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.posted_by = ?
        GROUP BY j.company_name
        ORDER BY applicant_count DESC
        LIMIT 5
    ''', (user_id,))
    companies_data = cursor.fetchall()
    
    conn.close()
    
    # Process status counts
    status_dict = {status: count for status, count in status_counts}
    pending_count = status_dict.get('pending', 0)
    accepted_count = status_dict.get('accepted', 0)
    rejected_count = status_dict.get('rejected', 0)
    
    # Process timeline data
    timeline_labels = [date for date, _ in timeline_data]
    timeline_counts = [count for _, count in timeline_data]
    
    # Process companies data
    company_labels = [company for company, _ in companies_data]
    company_counts = [count for _, count in companies_data]
    
    return render_template('analytics.html',
                         total_jobs=total_jobs,
                         total_applicants=total_applicants,
                         average_match_rate=round(avg_match, 1),
                         pending_count=pending_count,
                         accepted_count=accepted_count,
                         rejected_count=rejected_count,
                         timeline_labels=timeline_labels,
                         timeline_counts=timeline_counts,
                         company_labels=company_labels,
                         company_counts=company_counts)

def update_existing_jobs():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE jobs SET posted_date = CURRENT_TIMESTAMP WHERE posted_date IS NULL')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    app.run(debug=True)