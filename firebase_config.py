import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import pyrebase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Firebase Admin SDK Configuration
cred = credentials.Certificate({
    "type": os.getenv('FIREBASE_TYPE'),
    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY'),
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
    "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_CERT_URL'),
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
})

# Initialize Firebase Admin
try:
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
    })
except ValueError:
    # App already initialized
    pass

# Get Firestore database instance
db = firestore.client()

# Pyrebase Configuration for client-side operations
firebase_config = {
    "apiKey": os.getenv('FIREBASE_API_KEY'),
    "authDomain": os.getenv('FIREBASE_AUTH_DOMAIN'),
    "projectId": os.getenv('FIREBASE_PROJECT_ID'),
    "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET'),
    "messagingSenderId": os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    "appId": os.getenv('FIREBASE_APP_ID'),
    "databaseURL": os.getenv('FIREBASE_DATABASE_URL')
}

# Initialize Pyrebase
firebase = pyrebase.initialize_app(firebase_config)
auth_instance = firebase.auth()
storage_instance = firebase.storage()
