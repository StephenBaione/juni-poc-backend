from dotenv import load_dotenv
load_dotenv()

import firebase_admin

from firebase_admin import credentials, storage

import io
import os

from .result_objects.storage_results import FileOperationResult

class FirebaseStorage:
    firebase_app_initialized = False
    STORAGE_BUCKET = 'gs://personamatic.appspot.com'

    def __init__(self) -> None:
        load_dotenv()

        if not firebase_admin._apps:
            FirebaseStorage._load_firebase()

        FirebaseStorage.firebase_app_initialized = True

    @staticmethod
    def _load_firebase():
        cred_path = os.getenv('GOOGLE_FIREBASE_CREDENTIALS_PATH')

        # Fix for running with debug
        if cred_path.startswith('/creds'):
            cred_path = cred_path[1:]

        cred_path = os.path.join(os.path.dirname(__file__), '..', '..', cred_path)
        cred = credentials.Certificate(
            cred_path
        )
        firebase_admin.initialize_app(cred)

    @staticmethod
    def upload_file(storage_bucket, file_path, file_name):
        bucket = storage.bucket(storage_bucket)
        blob = bucket.blob(file_name)

        blob.upload_from_filename(file_path)

    @staticmethod
    def upload_file_from_bytes(storage_bucket, file_name: str, file_bytes: io.BytesIO):
        bucket = storage.bucket('personamatic.appspot.com')
        blob = bucket.blob(file_name)

        file_bytes.seek(0)

        try:
            blob.upload_from_file(file_bytes)
            return FileOperationResult(
                success=True, 
                message='File uploaded successfully', 
                file_name=file_name, 
                data=None
            )
        except Exception as e:
            return FileOperationResult(
                success=False,
                message=f'Error uploading file: {e}', 
                file_name=file_name, 
                data=None
            )
