from flask import Flask, render_template, request, jsonify, url_for, redirect, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
try:
    from .database import db
    from .pdf_utils import generate_prediction_report, format_report_datetime, short_report_id
except Exception:
    from database import db
    from pdf_utils import generate_prediction_report, format_report_datetime, short_report_id
import uuid
from datetime import datetime

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')
app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth'

# Register admin blueprint
from .admin.routes import admin_bp
app.register_blueprint(admin_bp)

try:
    db.ensure_prediction_schema()
except Exception:
    pass

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, email, role='user'):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    user = db.get_user_by_id(user_id)
    if user:
        return User(user['id'], user['username'], user['email'], user.get('role', 'user'))
    return None


def _get_predict_from_input():
    """Import the ML pipeline lazily so app startup stays fast on Render."""
    try:
        from .predict import predict_from_input
    except Exception:
        from predict import predict_from_input
    return predict_from_input


@app.context_processor
def inject_current_year():
    from datetime import datetime
    return {'current_year': datetime.now().year}


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/auth')
def auth():
    return render_template('auth.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/healthz')
def healthz():
    return jsonify({'ok': True}), 200


@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'user').strip()

    # Validation
    import re
    if not username or not email or not password or not role:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    # Email must end with @gmail.com
    if not re.match(r"^[A-Za-z0-9._%+-]+@gmail\.com$", email):
        return jsonify({'success': False, 'message': 'enter valid email address'}), 400

    # Password: min 8 chars, at least 1 uppercase, 1 lowercase, 1 special char
    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
    if not re.search(r"[A-Z]", password):
        return jsonify({'success': False, 'message': 'Password must contain at least one uppercase letter'}), 400
    if not re.search(r"[a-z]", password):
        return jsonify({'success': False, 'message': 'Password must contain at least one lowercase letter'}), 400
    if not re.search(r"[^A-Za-z0-9]", password):
        return jsonify({'success': False, 'message': 'Password must contain at least one special character'}), 400

    result = db.register_user(username, email, password, role)
    return jsonify(result), 200 if result['success'] else 400


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400
    
    result = db.login_user(username, password)
    
    if result['success']:
        user = result.get('user')
        user_obj = User(user['id'], user['username'], user['email'], user.get('role', 'user'))
        login_user(user_obj)
        return jsonify({'success': True, 'message': 'Login successful'}), 200
    
    return jsonify(result), 401


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user)


@app.route('/predictor')
def predictor():
    # derive symptom options from dataset (Symptom_1..Symptom_N columns)
    try:
        symptoms = set()
        # from main dataset columns Symptom_*
        ds_path = os.path.join(base_dir, 'dataset', 'dataset.csv')
        if os.path.exists(ds_path):
            df = pd.read_csv(ds_path)
            symptom_cols = [c for c in df.columns if str(c).lower().startswith('symptom')]
            for c in symptom_cols:
                vals = df[c].dropna().astype(str).str.strip()
                symptoms.update([v for v in vals.unique() if v and v.lower() != 'nan'])

        # from Symptom-severity.csv (column 'Symptom')
        sev_path = os.path.join(base_dir, 'dataset', 'Symptom-severity.csv')
        if os.path.exists(sev_path):
            sdf = pd.read_csv(sev_path)
            if 'Symptom' in sdf.columns:
                symptoms.update([str(v).strip() for v in sdf['Symptom'].dropna().unique() if str(v).strip()])

        symptoms = sorted(s for s in symptoms)
    except Exception:
        symptoms = []
    return render_template('predictor.html', symptoms=symptoms)


@app.route('/api/predict', methods=['POST'])
def api_predict():
    body = request.get_json() or {}
    symptoms = body.get('symptoms', {})
    patient_name = body.get('patient_name', 'Unknown')
    if not symptoms:
        return jsonify({'error': 'No symptoms provided'}), 400
    try:
        predict_from_input = _get_predict_from_input()
        res = predict_from_input(symptoms)
        if getattr(current_user, 'is_authenticated', False):
            user_id = current_user.id
        else:
            user_id = None
        report_id = str(uuid.uuid4())
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        symptom_names = list(symptoms.keys()) if isinstance(symptoms, dict) else []
        saved = db.save_prediction(
            user_id=user_id,
            report_id=report_id,
            patient_name=patient_name,
            predicted_disease=res.get('prediction'),
            recommended_tests=res.get('recommended_tests', []),
            symptoms=symptom_names,
        )
        res['report_id'] = report_id
        res['date'] = date
        res['patient_name'] = patient_name
        res['can_download_pdf'] = bool(user_id) and bool(saved)
        if res['can_download_pdf']:
            res['download_url'] = url_for('download_report', report_id=report_id)
        return jsonify(res)
    except FileNotFoundError as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"FileNotFoundError: {error_details}")
        return jsonify({'error': f'Required file not found: {str(e)}'}), 500
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Prediction error: {error_details}")  # Log to console for debugging
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


# Prediction history page
@app.route('/history')
@login_required
def prediction_history():
    history = db.get_prediction_history(current_user.id)
    return render_template('history.html', history=history, user=current_user)

# Download PDF report
@app.route('/download_report/<report_id>')
@login_required
def download_report(report_id):
    record = db.get_prediction_by_report_id(report_id, current_user.id)
    if not record:
        return "Report not found", 404
    date_disp = format_report_datetime(record['prediction_date'])
    pdf_buf = generate_prediction_report(
        report_id=record['report_id'],
        date_display=date_disp,
        patient_name=record['patient_name'] or '',
        predicted_disease=record['predicted_disease'],
        recommended_tests=record['recommended_tests'],
        symptoms=record.get('symptoms'),
    )
    pdf_buf.seek(0)
    fname = f"DiseasePredictionReport_{short_report_id(record['report_id'])}.pdf"
    return send_file(
        pdf_buf,
        as_attachment=True,
        download_name=fname,
        mimetype='application/pdf',
    )

@app.route('/api/debug/symptoms', methods=['GET'])
def debug_symptoms():
    """Debug endpoint to check available symptoms"""
    try:
        symptoms = set()
        ds_path = os.path.join(base_dir, 'dataset', 'dataset.csv')
        if os.path.exists(ds_path):
            df = pd.read_csv(ds_path)
            symptom_cols = [c for c in df.columns if str(c).lower().startswith('symptom')]
            for c in symptom_cols:
                vals = df[c].dropna().astype(str).str.strip()
                symptoms.update([v for v in vals.unique() if v and v.lower() != 'nan'])

        sev_path = os.path.join(base_dir, 'dataset', 'Symptom-severity.csv')
        if os.path.exists(sev_path):
            sdf = pd.read_csv(sev_path)
            if 'Symptom' in sdf.columns:
                symptoms.update([str(v).strip() for v in sdf['Symptom'].dropna().unique() if str(v).strip()])

        symptoms = sorted(s for s in symptoms)
        return jsonify({'symptoms': symptoms, 'count': len(symptoms)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=True)
