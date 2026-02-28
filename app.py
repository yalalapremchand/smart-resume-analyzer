from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import PyPDF2
import re

def has_skill(skill, text):
    pattern = r'\b' + re.escape(skill) + r'\b'
    return re.search(pattern, text) is not None
from PyPDF2.errors import PdfReadError
MASTER_SKILLS = {
    "frontend": {
        "html", "css", "javascript", "react", "redux",
        "responsive design", "bootstrap", "tailwind", "git"
    },
    "backend": {
        "python", "flask", "django", "node", "express",
        "rest api", "authentication", "jwt"
    },
    "database": {
        "sql", "mysql", "postgresql", "mongodb"
    }
}

app = Flask(__name__)

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///resumes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Role → required skills mapping
ROLE_SKILL_MAP = {
    "Frontend Developer": MASTER_SKILLS["frontend"],
    "Backend Developer": MASTER_SKILLS["backend"] | MASTER_SKILLS["database"],
    "Full Stack Developer": (
        MASTER_SKILLS["frontend"] |
        MASTER_SKILLS["backend"] |
        MASTER_SKILLS["database"]
    ),
    "Data Analyst": {
        "python", "sql", "excel", "statistics", "pandas", "numpy"
    }
}

# Database model
class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    score = db.Column(db.Integer)
    role = db.Column(db.String(100))
    skills_found = db.Column(db.Text)
    missing_skills = db.Column(db.Text)

@app.route("/", methods=["GET", "POST"])
def home():
    skills = []
    score = 0
    role = "General"
    missing_skills = []

    frontend_skills = {"html", "css", "javascript", "react"}
    backend_skills = {"python", "java", "flask", "django", "node", "sql"}
    data_skills = {"python", "sql"}

    if request.method == "POST":
        file = request.files.get("resume")

        if not file or file.filename == "":
            return render_template(
                "index.html",
                skills=[],
                score=0,
                role="No File",
                missing_skills=["Please upload a PDF resume"]
            )

        # ---------- SAFE PDF TEXT EXTRACTION ----------
        text = ""
        try:
            file.stream.seek(0)
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
        except PdfReadError:
            return render_template(
                "index.html",
                skills=[],
                score=0,
                role="Invalid PDF",
                missing_skills=["Upload a valid PDF file"]
            )

        text = text.lower()

        # ---------- SKILL EXTRACTION ----------
        skill_keywords = frontend_skills | backend_skills | data_skills
        found_skills = set()

        for skill in skill_keywords:
            required_skills = ROLE_SKILL_MAP.get(role, set())

            missing_skills = sorted([
    skill for skill in required_skills
    if skill not in skills_set
        ])
            for skill in skill_keywords:
                if has_skill(skill, text):
                    found_skills.add(skill.lower())
                    found_skills.add(skill.capitalize())

        skills = sorted(found_skills)

        # ---------- SCORE ----------
        skill_weights = {
            "html": 10,
            "css": 10,
            "javascript": 15,
            "react": 20,
            "python": 15,
            "java": 15,
            "flask": 20,
            "django": 20,
            "node": 15,
            "sql": 15
        }

        score = 0
        for s in skills:
            score += skill_weights.get(s.lower(), 3)
        score = min(score, 100)

        # ---------- ROLE DECISION ----------
        skills_set = {s.lower() for s in skills}

        if {"python", "django", "sql"}.issubset(skills_set):
            role = "Backend Developer"
        elif {"react", "javascript", "html", "css"}.issubset(skills_set):
            role = "Frontend Developer"
        elif {"python", "javascript", "react", "sql"}.issubset(skills_set):
            role = "Full Stack Developer"
        elif {"python", "sql"}.issubset(skills_set):
            role = "Data Analyst"
        else:
            role = "General"

        # ---------- SMART MISSING SKILLS ----------
        required_skills = ROLE_SKILL_MAP.get(role, set())

        missing_skills = sorted([
    skill for skill in required_skills
    if skill not in skills_set
])

        # ---------- SAVE TO DATABASE ----------
        resume_entry = Resume(
            filename=file.filename,
            score=score,
            role=role,
            skills_found=", ".join(skills),
            missing_skills=", ".join(missing_skills)
        )

        db.session.add(resume_entry)
        db.session.commit()

    return render_template(
        "index.html",
        skills=skills,
        score=score,
        role=role,
        missing_skills=missing_skills
    )

@app.route("/history")
def history():
    resumes = Resume.query.order_by(Resume.id.desc()).all()
    return render_template("history.html", resumes=resumes)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)