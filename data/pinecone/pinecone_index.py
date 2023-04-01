from pydantic import BaseModel

from dotenv import load_dotenv

import os

from typing import Optional

from uuid import uuid4

class PineConeIndex(BaseModel):
    id: Optional[str] = None
    if id is None:
        id = str(uuid4())

    index_name: str
    environment_name: str = os.getenv('PINECONE_ENVIRONMENT')
    dimensions: int
    pod_type: str
    pods_per_replica: int
    replicas: int
    total_pods: int
    metric: str = 'cosine'

    def set_id(self):
        self.id = str(uuid4())

    def to_dynamo_object(self):
        return {
            '_id': {
                'S': self._id
            },
            'index_name': {
                'S': self.index_name
            },
            'environment_name': {
                'S': self.environment_name
            },
            'dimensions': {
                'N': self.dimensions
            },
            'pod_type': {
                'S': self.pod_type
            },
            'pods_per_replica': {
                'S': self.pods_per_replica
            },
            'replicas': {
                'S': self.replicas
            },
            'total_pods': {
                'S': self.total_pods
            },
            'metric': {
                'S': self.metric
            }
        }

