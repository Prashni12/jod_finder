"""from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os, re, requests, uuid, secrets, logging
import PyPDF2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()  # Loads DATABASE_URL from your .env file

app = Flask(__name__)

# Uses your Neon database if available, otherwise falls back to local SQLite
database_url = os.environ.get("DATABASE_URL", "sqlite:///job_recommender.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)

# Database
# db_path = os.path.join(app.root_path, 'job_recommender.db')
# app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Uploads
# UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
#ALLOWED_EXTENSIONS = {'pdf'}

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resumes = db.relationship('Resume', backref='user', lazy=True)
    

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ---------- Helpers ----------
"""


from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os, re, requests, uuid, secrets, logging
import PyPDF2
from datetime import datetime
from dotenv import load_dotenv

# 1. Load environment variables from .env
load_dotenv()

# 2. Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 3. Initialize Flask app ONCE
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)

# 4. Configure Neon PostgreSQL Database (with local SQLite fallback)
database_url = os.environ.get("DATABASE_URL") or "sqlite:///job_recommender.db"
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)


app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 5. Uploads configuration (kept active for PDF resumes)
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf'}

# 6. Initialize SQLAlchemy ONCE
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resumes = db.relationship('Resume', backref='user', lazy=True)
    

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            logger.info(f"Extracted {len(text)} chars from {filepath}")
            return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""

def clean_html(raw_text):
    if not raw_text:
        return ""
    text = re.sub(r"<.*?>", "", raw_text)   # remove tags
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"[\n\r]+", " ", text)     # collapse newlines/carriage returns

    text = re.sub(r"\s+", " ", text)        # collapse spaces
    return text.strip()

# Skill mapping
SKILL_TO_CATEGORY = {
    "java": ["Backend", "Software Engineer"],
    "spring": ["Backend"],
    "python": ["Backend", "Data/ML"],
    "django": ["Backend", "Web Developer"],
    "flask": ["Backend", "Web Developer"],
    "node": ["Backend", "Web Developer"],
    "express": ["Backend", "Web Developer"],
    "sql": ["Data", "Database", "Backend"],
    "javascript": ["Frontend", "Web Developer"],
    "react": ["Frontend", "Web Developer"],
    "angular": ["Frontend"],
    "vue": ["Frontend"],
    "html": ["Frontend"],
    "css": ["Frontend"],
    "machine learning": ["Data Scientist", "AI"],
    "pandas": ["Data Analyst"],
    "tensorflow": ["AI"],
    "pytorch": ["AI"],
    "aws": ["Cloud Engineer"],
    "azure": ["Cloud Engineer"],
    "gcp": ["Cloud Engineer"],
    "docker": ["DevOps"],
    "kubernetes": ["DevOps"],
    "excel": ["Business/Finance"],
    "bcom": ["Business/Finance"],
    "accounting": ["Business/Finance"],
    "finance": ["Business/Finance"],    
    "c++": ["Backend", "Software Engineer"],
    "c#": ["Backend", "Software Engineer"],
    "MBA": ["Business/Finance","Human Resources","Marketing","Sales","Management","Project Management","Analytics"],
    "data analysis": ["Data Analyst"],
    "data science": ["Data Scientist"],
    "devops": ["DevOps"],

}

SKILLS_DETECT = sorted(list(SKILL_TO_CATEGORY.keys()), key=lambda x: -len(x))

def extract_skills(text):
    found = set()
    t = (text or "").lower()
    for kw in SKILLS_DETECT:
        if re.search(r'\b' + re.escape(kw) + r'\b', t):
            found.add(kw)
    if re.search(r'\bb\s*com\b', t):
        found.add('bcom')
    return sorted([s.title() for s in found])

def map_skills_to_roles(skills):
    categories = []
    for s in (skills or []):
        key = s.lower()
        if key in SKILL_TO_CATEGORY:
            for cat in SKILL_TO_CATEGORY[key]:
                if cat not in categories:
                    categories.append(cat)
    roles = []
    if "Frontend" in categories: roles.append("Frontend Developer")
    if "Backend" in categories: roles.append("Backend Developer")
    if "Data" in categories or "AI" in categories: roles.append("Data Scientist / Analyst")
    if "Cloud Engineer" in categories: roles.append("Cloud Engineer")
    if "DevOps" in categories: roles.append("DevOps Engineer")
    if "Business/Finance" in categories: roles.append("Finance / B.Com Roles")
    if not roles: roles.append("")
    return roles, categories

def detect_experience_level(resume_text):
    text = (resume_text or "").lower()
    if "fresher" in text or "recent graduate" in text or "entry level" in text:
        return "Fresher"
    match = re.search(r'(\d+)\s*(?:\+?\s*years?|yrs?)', text)
    if match:
        years = int(match.group(1))
        if years <= 1: return "Fresher"
        elif years <= 3: return "Junior"
        elif years <= 6: return "Mid"
        else: return "Senior"
    return "Fresher"

def detect_education(resume_text):
    text = (resume_text or "").lower()
    
    # Priority based on level and technicality (higher-level first)
    degrees = {
        "PhD / Doctorate": ["phd", "doctorate"],
        "M.Tech / M.E / M.S": ["m\.?tech", "m\.?e", "m\.?s"],
        "B.Tech / B.E": ["b\.?tech", "b\.?e"],
        "MBA": ["mba"],
        "MCA / BCA": ["mca", "bca"],
        "B.Com / M.Com": ["b\.?com", "m\.?com"],
        "B.Sc / M.Sc": ["b\.?sc", "m\.?sc"],
        "Bachelor's Degree": ["bachelor", "ba "],
        "Master's Degree": ["master", "ma "]
    }
    
    for degree_name, keywords in degrees.items():
        for kw in keywords:
            # Use word boundaries (\b) and replace optional dots with regex (\.?\s*)
            # This handles "B.Tech", "BTech", "B Tech"
            regex_kw = r'\b' + kw.replace('.', r'\.?\s*') + r'\b'
            if re.search(regex_kw, text):
                return [degree_name] 
    
    return ["Not Specified"]

def calculate_resume_score(skills, education, experience):

    score = 0

    score += min(len(skills) * 5, 40)

    if education[0] != "Not Specified":
        score += 20

    if experience != "Fresher":
        score += 20

    score += 20

    return min(score, 100)

def detect_job_role(resume_text, skills):
    roles_by_text = []
    text = (resume_text or "").lower()
    if "data scientist" in text: roles_by_text.append("Data Scientist")
    if "web developer" in text: roles_by_text.append("Web Developer")
    if "frontend" in text: roles_by_text.append("Frontend Developer")
    if "backend" in text: roles_by_text.append("Backend Developer")
    if "project manager" in text: roles_by_text.append("Project Manager")
    mapped_roles, _ = map_skills_to_roles(skills)
    return roles_by_text + mapped_roles if roles_by_text else mapped_roles

def calculate_match_score(resume_skills, job_text):

    if not job_text:
        return 0

    job_text = job_text.lower()

    total_skills = len(resume_skills)
    matched_skills = 0

    for skill in resume_skills:
        if skill.lower() in job_text:
            matched_skills += 1

    if total_skills == 0:
        return 0

    score = (matched_skills / total_skills) * 100

    return round(score)

# ---------- Job APIs ----------

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY")

def build_query(skills, roles, experience, education):
    parts = []
    if skills: parts.append(" ".join(skills[:5]))
    if roles: parts.append(" ".join(roles[:2]))
    if experience == "Fresher": parts.append("fresher entry level graduate")
    elif experience == "Junior": parts.append("junior")
    elif experience in ("Mid", "Senior"): parts.append(experience.lower())
    if education and education[0] != "Not Specified": parts.append(education[0])
    return " ".join(parts) if parts else "developer"

def fetch_jobs_from_adzuna(skills, country="in", experience="Fresher", education=None, job_roles=None, max_results=10):
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.warning("Adzuna keys missing")
        return []
    query = build_query(skills, job_roles, experience, education)
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {"app_id": ADZUNA_APP_ID, "app_key": ADZUNA_APP_KEY, "results_per_page": max_results, "what": query}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            jobs = []
            for j in data.get("results", []):
                # Start Snippet Modification for explicit '...'
                full_snippet = clean_html(j.get("description", ""))
                # Limit the snippet length for display purposes, explicitly adding '...'
                snippet_display = full_snippet
                if len(snippet_display) > 220:
                    snippet_display = full_snippet[:220] + "..."
                # End Snippet Modification

                jobs.append({
                        "jobtitle": j.get("title", "N/A"),
                        "company": j.get("company", {}).get("display_name", "N/A"),
                        "location": j.get("location", {}).get("display_name", "N/A"),
                        "url": j.get("redirect_url", "#"),
                        "snippet": snippet_display,
                        "posted": j.get("created", datetime.now().strftime("%Y-%m-%d"))[:10],
                        "salary": f"{j.get('salary_min', 'N/A')} - {j.get('salary_max', 'N/A')} {j.get('salary_currency', '')}".strip()
                    })
            return jobs
    except Exception as e:
        logger.error(f"Adzuna fetch failed: {e}")
    return []

def fetch_jobs_from_jooble(skills, location="India", experience="Fresher", max_results=10):
    if not JOOBLE_API_KEY:
        logger.warning("Jooble key missing")
        return []
    url = f"https://jooble.org/api/{JOOBLE_API_KEY}"
    query = build_query(skills, None, experience, None)
    payload = {"keywords": query, "location": location, "page": 1, "results": max_results}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            jobs = []
            for j in data.get("jobs", []):
                # Start Snippet Modification for explicit '...'
                full_snippet = clean_html(j.get("snippet") or "")
                # Limit the snippet length for display purposes, explicitly adding '...'
                snippet_display = full_snippet
                if len(snippet_display) > 220:
                    snippet_display = full_snippet[:220] + "..."
                # End Snippet Modification

                jobs.append({
                    "jobtitle": j.get("title", "N/A"),
                    "company": j.get("company", "N/A"),
                    "location": j.get("location", "N/A"),
                    "url": j.get("link", "#"),
                    "snippet": snippet_display,
                    "salary": j.get("salary", "N/A"),
                    "posted": j.get("Created", "Recently")
                })
            return jobs
    except Exception as e:
        logger.error(f"Jooble fetch failed: {e}")
    return []

def fetch_jobs_from_jsearch(skills, location="India", max_results=10):
    if not JSEARCH_API_KEY:
        logger.warning("JSearch key missing")
        return []

    query = " ".join(skills) if skills else "developer"

    url = "https://jsearch.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    params = {
        "query": query,
        "page": "1",
        "num_pages": "1"
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)

        if r.status_code == 200:
            data = r.json()
            jobs = []

            for j in data.get("data", [])[:max_results]:
                jobs.append({
                    "jobtitle": j.get("job_title", "N/A"),
                    "company": j.get("employer_name", "N/A"),
                    "location": j.get("job_city", "N/A"),
                    "url": j.get("job_apply_link", "#"),
                    "snippet": j.get("job_description", "")[:220] + "...",
                    "salary": j.get("job_salary", "N/A"),
                    "posted": j.get("job_posted_at_datetime_utc", "Recently")
                })

            return jobs

    except Exception as e:
        logger.error(f"JSearch fetch failed: {e}")

    return []

# No dummy jobs function is included

# ---------- Routes ----------

@app.route('/index')
def index():
    """Renders the main landing page (index.html)."""
    return render_template("index.html")

@app.route('/')
def home():
    """Redirects to the appropriate page based on login and resume status."""
    if 'user_id' not in session:
        return redirect(url_for('index')) # Redirect to the new index route
    
    user_id = session['user_id']
    # Check if the user has any resumes uploaded
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
    
    if latest_resume:
        # Existing user with a resume, show recommendations
        return redirect(url_for('recommend_jobs'))
    else:
        # New user or existing user without any resumes, prompt to upload
        return redirect(url_for('upload_resume'))

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        if User.query.filter_by(username=u).first():
            flash("Username exists","error"); return render_template("signup.html")
        user = User(username=u, password=generate_password_hash(p))
        db.session.add(user); db.session.commit()
        flash("Account created! Please login.","success")
        return redirect(url_for("login"))
    return render_template("signup.html")


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password,p):
            session['user_id']=user.id; session['username']=user.username
            # Redirect to home, which will then decide based on resume existence
            return redirect(url_for("home")) 
        flash("Invalid credentials","error")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear(); flash("Logged out","info")
    return redirect(url_for("login"))

@app.route('/upload_resume', methods=['GET', 'POST'])
def upload_resume():
    if 'user_id' not in session:
        return redirect(url_for("login"))

    if request.method == 'POST':
        f = request.files.get("resume")
        if not f or not f.filename:
            flash("No file selected", "error")
            return redirect(request.url)
        if allowed_file(f.filename):
            safe_name = secure_filename(f.filename)
            fname = f"{uuid.uuid4().hex}_{safe_name}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            f.save(path)
            text = extract_text_from_pdf(path)
            db.session.add(Resume(filename=fname, extracted_text=text, user_id=session['user_id']))
            db.session.commit()
            flash("Resume uploaded successfully!", "success")
            return redirect(url_for("recommend_jobs"))
        else:
            flash("Only PDF files are allowed", "error")
            return redirect(request.url)
    return render_template("upload_resume.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/interview_prep")
def interview_prep():
    return render_template("interview_prep.html")

@app.route('/recommend_jobs', methods=['GET','POST'])
def recommend_jobs():

    if 'user_id' not in session:
        return redirect(url_for("login"))

    latest = Resume.query.filter_by(user_id=session['user_id']).order_by(Resume.uploaded_at.desc()).first()

    if not latest:
        return redirect(url_for("upload_resume"))

    # ---------- DEFAULT VALUES ----------
    skills = extract_skills(latest.extracted_text)
    roles = detect_job_role(latest.extracted_text, skills)
    location = "India"
    job_type = ""
    exp_filter = ""

    # ---------- FILTER FORM ----------
    if request.method == "POST":

        skills = [s.strip() for s in request.form.get("skills","").split(",") if s.strip()]
        roles = [r.strip() for r in request.form.get("roles","").split(",") if r.strip()]

        location = request.form.get("location","India")
        job_type = request.form.get("job_type","")
        exp_filter = request.form.get("experience_level","")

    # ---------- RESUME ANALYSIS ----------
    exp = detect_experience_level(latest.extracted_text)
    edu = detect_education(latest.extracted_text)
    resume_score = calculate_resume_score(skills, edu, exp)

    if exp_filter:
        exp = exp_filter

    # ---------- FETCH JOBS FROM APIs ----------
    adzuna_jobs = fetch_jobs_from_adzuna(
        skills,
        "in",
        exp,
        edu,
        roles,
        max_results=10
    )

    jooble_jobs = fetch_jobs_from_jooble(
        skills,
        location,
        exp,
        max_results=10
    )

    jsearch_jobs = fetch_jobs_from_jsearch(
        skills,
        location,
        max_results=10
    )

    # ---------- COMBINE JOBS ----------
    job_list = adzuna_jobs + jooble_jobs + jsearch_jobs

    # ---------- MATCH SCORE ----------
    for job_item in job_list:
        job_item["match_score"] = calculate_match_score(
            skills,
            job_item.get("snippet","")
        )

    # ---------- REMOVE DUPLICATES ----------
    seen = set()
    jobs = []

    for job in job_list:
        key = (job["jobtitle"], job["company"])

        if key not in seen:
            seen.add(key)
            jobs.append(job)

    # ---------- PREVIEW ----------
    preview = clean_html(
        (latest.extracted_text[:800]+"...")
        if latest.extracted_text else "(No text)"
    )

    keyword_str = "%20".join(skills) if skills else "developer"

    linkedin = f"https://www.linkedin.com/jobs/search/?keywords={keyword_str}"
    naukri = f"https://www.naukri.com/{'-'.join(skills)}-jobs" if skills else "https://www.naukri.com/jobs"
    indeed = f"https://in.indeed.com/jobs?q={keyword_str}"
    glassdoor = f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={keyword_str}"

    freelance_query = "+".join(skills)

    upwork_url = f"https://www.upwork.com/nx/search/jobs/?q={freelance_query}"
    freelancer_url = f"https://www.freelancer.com/jobs/{skills[0].lower()}/" if skills else "https://www.freelancer.com/jobs/"
    fiverr_url = f"https://www.fiverr.com/search/gigs?query={freelance_query}"

    return render_template(
        "recommend_jobs.html",
        jobs=jobs,
        job_list=job_list,
        skills=skills,
        experience=exp,
        education=edu,
        job_roles=roles,
        resume_text_preview=preview,
        resume_score=resume_score,
        linkedin_url=linkedin,
        naukri_url=naukri,
        indeed_url=indeed,
        glassdoor_url=glassdoor,
        upwork_url=upwork_url,
        freelancer_url=freelancer_url,
        fiverr_url=fiverr_url,
        #resume_score=resume_score,
        location=location,
        job_type=job_type,
       
        
    )


def init_db():
    with app.app_context(): db.create_all()

with app.app_context():
    db.create_all()

if __name__=="__main__":
    init_db()
    app.run(debug=True)