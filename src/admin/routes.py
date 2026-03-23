import os
import threading
import json
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

try:
    from ..database import db
    from .dataset_utils import (
        add_disease_to_dataset,
        delete_disease_from_dataset,
        get_all_dataset_diseases,
        get_all_symptoms,
        get_dataset_stats,
        get_dataset_path,
        get_severity_path,
    )
except ImportError:
    from database import db
    from admin.dataset_utils import (
        add_disease_to_dataset,
        delete_disease_from_dataset,
        get_all_dataset_diseases,
        get_all_symptoms,
        get_dataset_stats,
        get_dataset_path,
        get_severity_path,
    )

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ── Training state ────────────────────────────────────────────────────────────
_training_lock = threading.Lock()
_training_state = {
    'status': 'idle',   # idle | running | done | error
    'started_at': None,
    'finished_at': None,
    'error': None,
}


def _admin_only():
    """Return True if access should be denied."""
    return not hasattr(current_user, 'role') or current_user.role != 'admin'


# ── Pages ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@login_required
def admin_dashboard():
    if _admin_only():
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('dashboard'))

    project_root = _project_root()
    dataset_path = get_dataset_path(project_root)
    severity_path = get_severity_path(project_root)

    stats = get_dataset_stats(dataset_path, severity_path)
    diseases = get_all_dataset_diseases(dataset_path)

    # last model retrain time
    model_path = os.path.join(project_root, 'models', 'xgb_model.joblib')
    last_trained = None
    if os.path.exists(model_path):
        ts = os.path.getmtime(model_path)
        last_trained = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        diseases=diseases,
        last_trained=last_trained,
        training_state=_training_state,
    )


@admin_bp.route('/add_disease', methods=['GET', 'POST'])
@login_required
def add_disease():
    if _admin_only():
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('dashboard'))

    project_root = _project_root()
    dataset_path = get_dataset_path(project_root)
    severity_path = get_severity_path(project_root)
    existing_symptoms = get_all_symptoms(dataset_path, severity_path)

    if request.method == 'POST':
        name = (request.form.get('disease_name') or '').strip()
        description = (request.form.get('description') or '').strip()
        symptoms = (request.form.get('symptoms') or '').strip()

        errors = []
        if not name:
            errors.append('Disease name is required.')
        if not symptoms:
            errors.append('At least one symptom is required.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/add_disease.html', existing_symptoms=existing_symptoms)

        # Add to dataset CSV
        ok, err_msg = add_disease_to_dataset(name, description, symptoms, dataset_path)

        # Try to add to DB (non-fatal)
        db.add_disease(name, description)

        if ok:
            flash(f'Disease "{name}" added successfully! Retrain the model to apply changes.', 'success')
        else:
            flash(f'Error updating CSV: {err_msg}', 'danger')

        return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin/add_disease.html', existing_symptoms=existing_symptoms)


# ── API endpoints ─────────────────────────────────────────────────────────────

@admin_bp.route('/retrain', methods=['POST'])
@login_required
def retrain_model():
    if _admin_only():
        return jsonify({'success': False, 'message': 'Admins only'}), 403

    with _training_lock:
        if _training_state['status'] == 'running':
            return jsonify({'success': False, 'message': 'Training already in progress'}), 409
        _training_state['status'] = 'running'
        _training_state['started_at'] = datetime.now().isoformat()
        _training_state['finished_at'] = None
        _training_state['error'] = None

    thread = threading.Thread(target=_run_training, daemon=True)
    thread.start()
    return jsonify({'success': True, 'message': 'Training started'})


@admin_bp.route('/training_status', methods=['GET'])
@login_required
def training_status():
    if _admin_only():
        return jsonify({'success': False}), 403
    with _training_lock:
        state = dict(_training_state)
    return jsonify(state)


@admin_bp.route('/dataset_stats', methods=['GET'])
@login_required
def dataset_stats():
    if _admin_only():
        return jsonify({'success': False}), 403
    project_root = _project_root()
    stats = get_dataset_stats(get_dataset_path(project_root), get_severity_path(project_root))
    model_path = os.path.join(project_root, 'models', 'xgb_model.joblib')
    last_trained = None
    if os.path.exists(model_path):
        ts = os.path.getmtime(model_path)
        last_trained = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
    stats['last_trained'] = last_trained
    return jsonify(stats)


@admin_bp.route('/delete_disease', methods=['POST'])
@login_required
def delete_disease():
    if _admin_only():
        return jsonify({'success': False, 'message': 'Admins only'}), 403
    data = request.get_json() or {}
    disease_name = (data.get('disease_name') or '').strip()
    if not disease_name:
        return jsonify({'success': False, 'message': 'No disease name provided'}), 400

    project_root = _project_root()
    dataset_path = get_dataset_path(project_root)
    ok, msg = delete_disease_from_dataset(disease_name, dataset_path)

    # Also try removing from DB (non-fatal)
    try:
        conn = db.connect()
        if conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM diseases WHERE name = %s', (disease_name,))
            conn.commit()
            cur.close()
            conn.close()
    except Exception:
        pass

    return jsonify({'success': ok, 'message': msg})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _project_root():
    """Absolute path to the project root (parent of src/)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _run_training():
    """Background worker: run train() and update _training_state."""
    try:
        project_root = _project_root()
        dataset_path = get_dataset_path(project_root)
        severity_path = get_severity_path(project_root)
        models_dir = os.path.join(project_root, 'models')

        # Use a subprocess so there are no import path issues at all
        import subprocess
        import sys
        train_script = os.path.join(project_root, 'src', 'train.py')
        os.makedirs(models_dir, exist_ok=True)
        log_path = os.path.join(models_dir, 'training_subprocess.log')
        with open(log_path, 'w', encoding='utf-8') as lf:
            # Do not use capture_output=True: it can deadlock if subprocess stdout/stderr fills the buffer.
            result = subprocess.run(
                [
                    sys.executable,
                    train_script,
                    '--dataset',
                    dataset_path,
                    '--severity',
                    severity_path,
                    '--out',
                    models_dir,
                ],
                stdout=lf,
                stderr=lf,
                text=True,
            )
        if result.returncode != 0:
            # Include tail of the log for debugging.
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as rf:
                    tail = rf.read()[-4000:]
            except Exception:
                tail = ''
            raise RuntimeError(tail or 'Training subprocess failed')

        with _training_lock:
            _training_state['status'] = 'done'
            _training_state['finished_at'] = datetime.now().isoformat()
    except Exception as exc:
        with _training_lock:
            _training_state['status'] = 'error'
            _training_state['finished_at'] = datetime.now().isoformat()
            # Keep error payload small for frontend JSON polling.
            msg = str(exc)
            msg = msg.replace('\r', ' ').replace('\n', ' ')
            if len(msg) > 1200:
                msg = msg[-1200:]
            _training_state['error'] = msg
        print(f"[Admin] Training error (preview): {_training_state.get('error')}")
