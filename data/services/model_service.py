from data.models.model import Model

from data.firebase.firebase_db import FireBaseDB

class ModelService:
    firebase_db = FireBaseDB('test')

    def __init__(self) -> None:
        pass

    def add_model(self, model: Model):
        self.firebase_db.set_data('model', dict(model))

