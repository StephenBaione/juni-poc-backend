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

    @staticmethod
    def from_dict(pineconde_index_as_dict: dict) -> "PineConeIndex":
        # Required values
        index_name = pineconde_index_as_dict['index_name']
        dimensions = pineconde_index_as_dict['dimensions']
        pod_type = pineconde_index_as_dict['pod_type']
        pods_per_replica = pineconde_index_as_dict['pods_per_replica']
        replicas = pineconde_index_as_dict['replicas']
        total_pods = pineconde_index_as_dict['total_pods']

        # Optional Values
        _id = pineconde_index_as_dict.get('id', None)

        return PineConeIndex(
            id=_id,
            index_name=index_name,
            dimensions=dimensions,
            pod_type=pod_type,
            pods_per_replica=pods_per_replica,
            replicas=replicas,
            total_pods=total_pods
        )

    def set_id(self):
        self.id = str(uuid4())
