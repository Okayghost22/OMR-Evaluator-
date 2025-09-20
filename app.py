from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy 
import os
import json
import uuid 
from omr_processor import process_omr_sheet

app = Flask(__name__, static_folder='uploads')
app.secret_key = 'c8dfed82bb85d4896a4e5a495e0d7457913136bebd2c6b8a' 

# === Database Configuration ===
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///results.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# === Database Model ===
class OMRResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), unique=True, nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
    subject_scores = db.Column(db.Text, nullable=False) 
    answers = db.Column(db.Text, nullable=False)
    annotated_image_path = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part"
    file = request.files["file"]
    if file.filename == "":
        return "No selected file"
    
    exam_set = request.form.get("exam_set")

    if file:
        upload_folder = "uploads"
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        unique_filename = str(uuid.uuid4()) + "_" + file.filename
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        result = process_omr_sheet(file_path, exam_set)

    if result["status"] == "success":
        subject_scores_str = json.dumps(result["subject_scores"])
        answers_str = json.dumps(result["answers"])
        
        new_result = OMRResult(
            filename=unique_filename,
            total_score=result["total_score"],
            subject_scores=subject_scores_str,
            answers=answers_str,
            annotated_image_path=os.path.basename(result["annotated_image_path"])
        )
        db.session.add(new_result)
        db.session.commit()

        session['result_id'] = new_result.id
        
        return render_template(
            "results.html", 
            answers=result["answers"],
            total_score=result["total_score"],
            subject_scores=result["subject_scores"],
            annotated_image_path=os.path.basename(result["annotated_image_path"])
        )
    else:
        return result["message"]

@app.route("/summary")
def show_summary():
    result_id = session.get('result_id')
    if not result_id:
        return "No results found. Please evaluate a sheet first."
    
    result_record = OMRResult.query.get_or_404(result_id)

    subject_scores = json.loads(result_record.subject_scores)

    return render_template(
        "summary.html",
        total_score=result_record.total_score,
        subject_scores=subject_scores
    )

# === New routes for login and logout ===
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Hardcoded credentials
        if username == "evaluator" and password == "password123":
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# === Protected Dashboard Route ===
@app.route("/dashboard")
def dashboard():
    # Check if the user is logged in
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))

    all_results = OMRResult.query.all()
    
    dashboard_data = []
    for res in all_results:
        subject_scores = json.loads(res.subject_scores)
        dashboard_data.append({
            'id': res.id,
            'filename': res.filename,
            'total_score': res.total_score,
            'subject_scores': subject_scores,
            'timestamp': res.timestamp
        })
    
    return render_template('dashboard.html', dashboard_data=dashboard_data)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)