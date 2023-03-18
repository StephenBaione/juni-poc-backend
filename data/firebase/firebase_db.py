import os
from dotenv import load_dotenv

import firebase_admin

from firebase_admin import credentials, db, firestore

import typing

import enum

class QueryOperators(enum.Enum):
    LESS_THAN = '<'
    LESS_THAN_OR_EQUAL_TO = '<='
    EQUAL_TO = '=='
    GREATER_THAN = '>'
    GREATER_THAN_OR_EQUAL_TO = '>='
    NOT_EQUAL_TO = '!='
    ARRAY_CONTAINS = 'array_contains'
    ARRAY_CONTAINS_ANY = 'array_contains_any'
    IN = 'in'
    NOT_IN = 'not_in'

class FireBaseDB:
    firebase_app_initialized = False
    firestore_db = None

    loaded_collections = {}

    def __init__(self, username) -> None:
        load_dotenv()

        self.username = username

        if not FireBaseDB.firebase_app_initialized:
            FireBaseDB._load_db()
            FireBaseDB.firebase_app_initialized = True

        if FireBaseDB.firestore_db is None:
            FireBaseDB.firestore_db = firestore.client()

    @staticmethod
    def _load_db():
        cred = credentials.Certificate(
            os.getenv('GOOGLE_FIREBASE_CREDENTIALS_PATH')
        )
        firebase_admin.initialize_app(cred)

    @staticmethod
    def load_collection(collection_name):
        if FireBaseDB.loaded_collections.get(collection_name) is None:
            FireBaseDB.loaded_collections[collection_name] = FireBaseDB.firestore_db.collection(collection_name)

        return FireBaseDB.loaded_collections.get(collection_name, None)
    
    @staticmethod
    def set_data(collection_name, data):
        collection = FireBaseDB.load_collection(collection_name)
        collection.document(data['id']).set(data)

    @staticmethod
    def get_data(collection_name, id):
        collection = FireBaseDB.load_collection(collection_name)
        document_ref = collection.document(id)

        if document_ref.exists:
            return document_ref.to_dict()
        
        return None
    
    @staticmethod
    def get_simple_query(collection_name, field, expression, value) -> typing.Generator:
        collection = FireBaseDB.load_collection(collection_name)

        return collection.where(field, expression, value).stream()
    
    @staticmethod
    def get_all_docs(collection_name) -> typing.Generator:
        collection = FireBaseDB.load_collection(collection_name)
        return collection.stream()
    


