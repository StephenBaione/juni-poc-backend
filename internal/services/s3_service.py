from .boto3_service import Boto3Service, ResourceClients

from boto3.dynamodb.conditions import Key

import os

import pydantic

from typing import Optional, Any, List, Union, Dict, Tuple

from PIL import Image
from io import BytesIO
import numpy as np

class S3Service:
    _boto3_service = Boto3Service()
    _s3_resource = None

    def __init__(self, bucket_name=os.getenv('AWS_DEFAULT_BUCKET_NAME'), region_name=os.getenv('AWS_DEFAULT_REGION')) -> None:
        S3Service.set_s3_resource(region_name)

        self.bucket_name = bucket_name

    @staticmethod
    def set_s3_resource(region_name: str):
        S3Service._s3_resource = S3Service._boto3_service.get_resource(ResourceClients.S3, region_name)

    def get_image(self, key: str):
        if S3Service._s3_resource is None:
            self.set_s3_resource()
        
        try:
            bucket = self._s3_resource.Bucket(self.bucket_name)
            object = bucket.Object(key)
            response = object.get()
            file_stream = response['Body']
            image = Image.open(file_stream)
            image_array = np.array(image)
            return image_array
        except Exception as e:
            pass