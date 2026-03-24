# MongoDB Setup Guide

This project now uses MongoDB for authentication, disease metadata, and prediction history. That fits Render deployment better because the app only needs a single `MONGODB_URI` secret instead of a self-managed MySQL service.

## Prerequisites

1. Python 3.7+
2. A MongoDB database
   Options:
   - Local MongoDB for development
   - MongoDB Atlas for production/Render

## Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages:
- `pymongo[srv]` for MongoDB connections, including Atlas SRV URIs
- `Flask-Login` for sessions
- `werkzeug` for password hashing

## Configure Environment Variables

### PowerShell

```powershell
$env:MONGODB_URI = "mongodb://localhost:27017/disease_recognition"
$env:MONGO_DB_NAME = "disease_recognition"
$env:SECRET_KEY = "your-secret-key-change-in-production"
```

### Bash

```bash
export MONGODB_URI="mongodb://localhost:27017/disease_recognition"
export MONGO_DB_NAME="disease_recognition"
export SECRET_KEY="your-secret-key-change-in-production"
```

Notes:
- If your URI already includes the database name, `MONGO_DB_NAME` is optional.
- For MongoDB Atlas, your URI will usually look like `mongodb+srv://...`.

## Initialize Indexes

```bash
python init_db.py
```

This creates the MongoDB indexes the app expects:
- unique username
- unique email
- unique disease name
- unique report id
- prediction history lookup indexes

## Run the App

```bash
python -m src.app
```

The app runs on `http://localhost:8000` by default.

## Render Deployment

Render's current docs support two practical MongoDB approaches for this app:

1. Deploy this Flask app on Render and connect it to MongoDB Atlas.
2. Or run MongoDB on Render as a private Docker service backed by a persistent disk.

For the simplest app deployment flow, Atlas is usually easiest:

1. Deploy this Flask app on Render.
2. Create a MongoDB Atlas cluster.
3. Add `MONGODB_URI` and `SECRET_KEY` as Render environment variables.
4. Optionally add `MONGO_DB_NAME` if your URI does not specify it.

If you host MongoDB on Render itself, make sure the database service uses a persistent disk because Render web services otherwise use an ephemeral filesystem.

## Stored Collections

The app uses these MongoDB collections:
- `users`
- `diseases`
- `prediction_history`

## Troubleshooting

### Could not connect to MongoDB
- Check that `MONGODB_URI` is correct.
- If using Atlas, confirm your IP/network access rules allow Render or your local machine.
- Make sure the database user/password in the URI are valid.

### Duplicate username or email
- MongoDB unique indexes enforce this now.
- Try a different username/email or remove the old record from the `users` collection.

### Atlas SRV URI issues
- Make sure `pymongo[srv]` is installed from `requirements.txt`.
- Confirm the URI starts with `mongodb+srv://` if you copied an SRV connection string.

### Existing MySQL data
- This code change does not automatically migrate old MySQL records into MongoDB.
- If you need that preserved, the data should be exported from MySQL and imported into the MongoDB collections separately.

## Production Notes

1. Set a strong random `SECRET_KEY`.
2. Keep MongoDB credentials in environment variables only.
3. Restrict your MongoDB network access rules.
4. Use a managed MongoDB service for production reliability.
