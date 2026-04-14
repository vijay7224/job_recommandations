from flask import Flask, render_template, request, redirect, url_for, session,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bson import ObjectId

# =======================
# FLASK SETUP
# =======================
app = Flask(__name__)
app.secret_key = 'secret123'

# =======================
# MONGODB CONNECTION
# =======================
client = MongoClient("mongodb+srv://vijaysuryawanshi7224_db_user:vijay%402005@cluster0.ckvnjfm.mongodb.net/collegedb?retryWrites=true&w=majority")
db = client["job_portal"]
users_collection = db["users"]
jobs_collection = db["jobs"]

# =======================
# PDF TEXT EXTRACT
# =======================
def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

# =======================
# JOB RECOMMENDATION ML
# =======================
def recommend_jobs(resume_text):
    jobs_data = list(jobs_collection.find())

    # Convert ObjectId to string
    for job in jobs_data:
        job["_id"] = str(job["_id"])

    job_texts = [job.get("Skills Required", "") for job in jobs_data]
    all_texts = [resume_text] + job_texts

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(all_texts)

    resume_vec = vectors[0]
    job_vecs = vectors[1:]

    scores = cosine_similarity(resume_vec, job_vecs)[0]

    # Add score
    for i, job in enumerate(jobs_data):
        job["Match Score (%)"] = float(scores[i] * 100)

    # Sort
    sorted_jobs = sorted(jobs_data, key=lambda x: x["Match Score (%)"], reverse=True)

    return sorted_jobs[:8]

# =======================
# HOME
# =======================
@app.route('/')
def home():
    return render_template('home.html')

# =======================
# REGISTER
# =======================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if users_collection.find_one({"email": email}):
            return "Email already exists"

        users_collection.insert_one({
            "username": username,
            "email": email,
            "password": password
        })

        return redirect(url_for('login'))

    return render_template('register.html')

# =======================
# LOGIN
# =======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users_collection.find_one({"email": email})

        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            return redirect(url_for('recommend'))
        else:
            return "Invalid login"

    return render_template('login.html')

# =======================
# LOGOUT
# =======================
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


@app.route('/job')
def job():
    return  render_template("job.html")
# =======================
# RECOMMEND
# =======================
@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'resume' not in request.files:
            return "No file uploaded"

        file = request.files['resume']

        if file.filename == '':
            return "No selected file"

        if not file.filename.endswith('.pdf'):
            return "Only PDF allowed"

        resume_text = extract_pdf_text(file)

        if resume_text.strip() == "":
            return "Empty resume"

        jobs = recommend_jobs(resume_text)

        return render_template('result.html', jobs=jobs)

    return render_template('recommend.html')




@app.route('/api/jobs')
def get_jobs():
    jobs = list(jobs_collection.find())

    # Convert ObjectId to string
    for job in jobs:
        job["_id"] = str(job["_id"])

    return jsonify(jobs)

# =======================
# RUN
# =======================
if __name__ == '__main__':
    app.run(debug=True)