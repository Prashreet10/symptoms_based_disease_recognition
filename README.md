# Symptoms-based Disease Prediction (XGBoost)

This project trains an XGBoost model to predict diseases from symptom inputs, using symptom severity and duration as weighted inputs, and provides explainability via feature importance and SHAP. It also recommends tests dynamically based on prediction confidence.

## ✨ New Features (v2.0)

**MySQL Authentication System** - Users can now:
- 📝 Sign up with username, email, and password
- 🔐 Login securely with password hashing
- 📊 Access personalized dashboard
- ⚙️ Manage account settings
- 🔒 Secure sessions with Flask-Login

👉 See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for setup and usage guides

## Quick Start

### For Authentication Setup (NEW)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment variables
$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_NAME = "symptom_predictor"

# 3. Initialize database
python init_db.py

# 4. Run application
python -m src.app
```
👉 See [QUICK_START.md](QUICK_START.md) for detailed instructions

### For Model Training (Original)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train the model
python src/train.py --dataset dataset/dataset.csv --severity dataset/Symptom-severity.csv --out models

# 3. Test prediction
python src/predict.py
```

Notes
- The preprocessing expects a label column named `prognosis`, `disease`, or `label` in `dataset/dataset.csv`.
- Symptom severity mapping should be in `dataset/Symptom-severity.csv` with columns `Symptom,Weight`.
- Test recommendations are sourced from `dataset/symptom_precaution.csv` (column `Precaution` expected). If that file doesn't map tests, recommendations will be empty.

Adjust `src/predict.py` and `src/preprocess.py` as needed to integrate with your web/mobile interface.

## 📚 Documentation

For complete information about the new authentication system:

| Document | Purpose |
|----------|---------|
| [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) | 📑 **Start here** - Documentation guide |
| [QUICK_START.md](QUICK_START.md) | ⚡ 5-minute setup guide |
| [DATABASE_SETUP.md](DATABASE_SETUP.md) | 📖 Detailed MySQL setup |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | 📋 Commands & API reference |
| [FEATURES_OVERVIEW.md](FEATURES_OVERVIEW.md) | 🎯 Feature descriptions |
| [FILE_CHANGES.md](FILE_CHANGES.md) | 💻 Code-level details |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | 📈 Architecture overview |

## 🔧 Project Structure

```
project/
├── src/
│   ├── app.py              ← Flask application with auth
│   ├── database.py         ← MySQL connectivity
│   ├── predict.py
│   ├── train.py
│   └── preprocess.py
├── templates/
│   ├── base.html           ← Navbar with login
│   ├── home.html           ← Home page
│   ├── auth.html           ← Login/signup forms
│   ├── dashboard.html      ← User dashboard
│   ├── settings.html       ← Account settings
│   ├── about.html
│   └── predictor.html
├── static/
│   ├── css/
│   ├── img/
│   └── js/
├── dataset/
│   └── *.csv
├── models/
│   └── *.joblib
├── requirements.txt
├── init_db.py              ← Database initialization
└── .env.example            ← Environment template
```

## 🔐 Security Features

✅ Password hashing with werkzeug  
✅ SQL injection prevention  
✅ Secure session management  
✅ Login-required route protection  
✅ Database connection security

## 🚀 Deployment

For production deployment:
1. Change `SECRET_KEY` to a random value
2. Enable HTTPS
3. Use strong database credentials
4. Set up environment variables properly
5. Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md#deployment-checklist)

## 📞 Support

- Setup issues → [DATABASE_SETUP.md](DATABASE_SETUP.md#troubleshooting)
- Feature questions → [FEATURES_OVERVIEW.md](FEATURES_OVERVIEW.md)
- Code questions → [FILE_CHANGES.md](FILE_CHANGES.md)
- API questions → [QUICK_REFERENCE.md](QUICK_REFERENCE.md#api-endpoints)
