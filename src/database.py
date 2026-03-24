import os
from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import ConfigurationError, DuplicateKeyError, PyMongoError
from werkzeug.security import check_password_hash, generate_password_hash


def _format_timestamp(value):
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


class Database:
    def __init__(self):
        self.uri = os.environ.get(
            "MONGODB_URI",
            os.environ.get("MONGO_URI", "mongodb://localhost:27017/disease_recognition"),
        )
        self.database_name = os.environ.get(
            "MONGO_DB_NAME",
            os.environ.get("DB_NAME", ""),
        )
        self.client = None
        self.db = None

    def connect(self):
        """Create and cache a MongoDB database handle."""
        if self.db is not None:
            return self.db

        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            if self.database_name:
                self.db = self.client[self.database_name]
            else:
                try:
                    self.db = self.client.get_default_database()
                except ConfigurationError:
                    self.db = None
                if self.db is None:
                    self.db = self.client["disease_recognition"]

            # Fail fast if the server is unreachable.
            self.client.admin.command("ping")
            return self.db
        except Exception as e:
            print(f"Error while connecting to MongoDB: {e}")
            self.client = None
            self.db = None
            return None

    def disconnect(self):
        """Close the MongoDB client."""
        if self.client is not None:
            self.client.close()
        self.client = None
        self.db = None

    def _users(self):
        database = self.connect()
        return database["users"] if database is not None else None

    def _diseases(self):
        database = self.connect()
        return database["diseases"] if database is not None else None

    def _history(self):
        database = self.connect()
        return database["prediction_history"] if database is not None else None

    def _normalize_user(self, document):
        if not document:
            return None
        return {
            "id": str(document["_id"]),
            "username": document.get("username", ""),
            "email": document.get("email", ""),
            "role": document.get("role", "user"),
            "created_at": document.get("created_at"),
        }

    def _normalize_prediction(self, document, for_history=False):
        if not document:
            return None

        record = {
            "id": str(document["_id"]),
            "report_id": document.get("report_id"),
            "user_id": document.get("user_id"),
            "patient_name": document.get("patient_name"),
            "predicted_disease": document.get("predicted_disease"),
            "recommended_tests": document.get("recommended_tests", []),
            "symptoms": document.get("symptoms", []),
            "prediction_date": document.get("prediction_date"),
        }

        if for_history:
            record["prediction_date"] = _format_timestamp(record["prediction_date"])
            record["recommended_tests"] = ", ".join(record["recommended_tests"])
            record["symptoms"] = ", ".join(record["symptoms"])

        return record

    def ensure_prediction_schema(self):
        """MongoDB is schemaless; we only ensure indexes exist."""
        self.init_db()

    def init_db(self):
        """Initialize collections and indexes."""
        try:
            users = self._users()
            diseases = self._diseases()
            history = self._history()
            if users is None or diseases is None or history is None:
                return

            users.create_index([("username_lower", ASCENDING)], unique=True)
            users.create_index([("email_lower", ASCENDING)], unique=True)
            diseases.create_index([("name_lower", ASCENDING)], unique=True)
            history.create_index([("report_id", ASCENDING)], unique=True)
            history.create_index([("user_id", ASCENDING), ("prediction_date", DESCENDING)])
            print("MongoDB indexes initialized successfully")
        except PyMongoError as e:
            print(f"Error initializing MongoDB: {e}")

    def add_disease(self, name, description):
        try:
            diseases = self._diseases()
            if diseases is None:
                return False

            now = datetime.utcnow()
            diseases.update_one(
                {"name_lower": name.strip().lower()},
                {
                    "$setOnInsert": {
                        "name": name.strip(),
                        "name_lower": name.strip().lower(),
                        "description": description,
                        "created_at": now,
                    }
                },
                upsert=True,
            )
            return True
        except Exception as e:
            print(f"Error adding disease: {e}")
            return False

    def delete_disease(self, name):
        try:
            diseases = self._diseases()
            if diseases is None:
                return False
            diseases.delete_one({"name_lower": name.strip().lower()})
            return True
        except Exception as e:
            print(f"Error deleting disease: {e}")
            return False

    def get_all_diseases(self):
        try:
            diseases = self._diseases()
            if diseases is None:
                return []

            results = diseases.find().sort("created_at", DESCENDING)
            return [
                {
                    "id": str(doc["_id"]),
                    "name": doc.get("name", ""),
                    "description": doc.get("description"),
                    "created_at": _format_timestamp(doc.get("created_at")),
                }
                for doc in results
            ]
        except Exception as e:
            print(f"Error fetching diseases: {e}")
            return []

    def save_prediction(
        self,
        user_id,
        report_id,
        patient_name,
        predicted_disease,
        recommended_tests,
        symptoms=None,
    ):
        try:
            history = self._history()
            if history is None:
                return False

            history.insert_one(
                {
                    "report_id": report_id,
                    "user_id": str(user_id) if user_id else None,
                    "patient_name": patient_name,
                    "predicted_disease": predicted_disease,
                    "recommended_tests": list(recommended_tests or []),
                    "symptoms": list(symptoms or []),
                    "prediction_date": datetime.utcnow(),
                }
            )
            return True
        except Exception as e:
            print(f"Error saving prediction: {e}")
            return False

    def get_prediction_history(self, user_id):
        try:
            history = self._history()
            if history is None:
                return []

            results = history.find({"user_id": str(user_id)}).sort("prediction_date", DESCENDING)
            return [self._normalize_prediction(doc, for_history=True) for doc in results]
        except Exception as e:
            print(f"Error fetching prediction history: {e}")
            return []

    def get_prediction_by_report_id(self, report_id, user_id):
        try:
            history = self._history()
            if history is None:
                return None

            result = history.find_one({"report_id": report_id, "user_id": str(user_id)})
            return self._normalize_prediction(result)
        except Exception as e:
            print(f"Error fetching prediction by report_id: {e}")
            return None

    def register_user(self, username, email, password, role="user"):
        """Register a new user."""
        try:
            users = self._users()
            if users is None:
                return {"success": False, "message": "Database connection failed"}

            username = username.strip()
            email = email.strip()
            user_doc = {
                "username": username,
                "username_lower": username.lower(),
                "email": email,
                "email_lower": email.lower(),
                "password": generate_password_hash(password),
                "role": role,
                "created_at": datetime.utcnow(),
            }
            users.insert_one(user_doc)
            return {"success": True, "message": "User registered successfully"}
        except DuplicateKeyError:
            return {"success": False, "message": "Username or email already exists"}
        except PyMongoError as e:
            return {"success": False, "message": f"Registration failed: {str(e)}"}

    def login_user(self, username, password):
        """Authenticate user."""
        try:
            users = self._users()
            if users is None:
                return {"success": False, "message": "Database connection failed"}

            user = users.find_one({"username_lower": username.strip().lower()})
            if user and check_password_hash(user["password"], password):
                normalized_user = self._normalize_user(user)
                return {
                    "success": True,
                    "message": "Login successful",
                    "user": {
                        "id": normalized_user["id"],
                        "username": normalized_user["username"],
                        "email": normalized_user["email"],
                        "role": normalized_user["role"],
                    },
                }
            return {"success": False, "message": "Invalid username or password"}
        except PyMongoError as e:
            return {"success": False, "message": f"Login failed: {str(e)}"}

    def get_user(self, username):
        """Get user by username."""
        try:
            users = self._users()
            if users is None:
                return None

            user = users.find_one({"username_lower": username.strip().lower()})
            return self._normalize_user(user)
        except PyMongoError as e:
            print(f"Error fetching user: {e}")
            return None

    def get_user_by_id(self, user_id):
        """Get user by ID."""
        try:
            users = self._users()
            if users is None:
                return None

            user = None
            if isinstance(user_id, ObjectId):
                user = users.find_one({"_id": user_id})
            elif ObjectId.is_valid(str(user_id)):
                user = users.find_one({"_id": ObjectId(str(user_id))})
            return self._normalize_user(user)
        except Exception as e:
            print(f"Error fetching user by ID: {e}")
            return None


db = Database()
