from .boto3_service import Boto3Service, ResourceClients

from boto3.dynamodb.conditions import Key

from .dynamodb_service import ItemCrudResponse

import os, io

import pydantic

from typing import Optional, Any, List, Union, Dict, Tuple

import os

from PIL import Image
from io import BytesIO
import numpy as np

from time import gmtime, strftime

AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
USER_FILES_BUCKET_NAME = os.getenv('AWS_USER_FILES_BUCKET_NAME')
USER_FILES_BUCKET_URL = os.getenv('AWS_USER_FILES_BUCKET_URL')
AVATAR_FOLDER = os.getenv('AWS_USER_FILES_BUCKET_AVATAR_FOLDER')
AVATAR_FOLDER_PATH = os.getenv('AWS_USER_FILES_BUCKET_AVATAR_FOLDER_PATH')
DEFAULT_AVATAR_URL = os.getenv('AWS_USER_FILES_BUCKET_AVATAR_DEFAULT_IMAGE_URL')

TIME_FORMAT_FILE_NAME = "%Y-%m-%d_%H:%M:%S"

class S3Service:
    _boto3_service = Boto3Service()
    _s3_resource = None

    def __init__(self, bucket_name=USER_FILES_BUCKET_NAME, region_name=AWS_DEFAULT_REGION) -> None:
        S3Service.set_s3_resource(region_name)

        self.bucket_name = bucket_name

    @staticmethod
    def set_s3_resource(region_name: str):
        S3Service._s3_resource = S3Service._boto3_service.get_resource(ResourceClients.S3, region_name)

    # given a key, return the image from S3 as a numpy array
    def get_image(self, key: str):
        if S3Service._s3_resource is None:
            self.set_s3_resource()
        
        try:
            # get the image from S3
            bucket = self._s3_resource.Bucket(self.bucket_name)
            object = bucket.Object(key)
            response = object.get()

            # convert the image to a numpy array
            file_stream = response['Body']
            image = Image.open(file_stream)
            image_array = np.array(image)

            return ItemCrudResponse(
                Item={image_array},
                success=True,
                exception=None
            )
        
        except Exception as e:
            print('Error getting image from S3: ', e)

            return ItemCrudResponse(
                Item={},
                success=False,
                exception=e
            )

    # given a user id and an image file, upload the image to S3 and return the url
    def upload_avatar(self, user_id: str, file: bytes):
        if S3Service._s3_resource is None:
            self.set_s3_resource()
        
        try:
            bucket = self._s3_resource.Bucket(self.bucket_name)
            
            # avatar will be stored in avatars/{user_id}/{timestamp}.png
            # each file name must be unique so that the front end updates the image with the new URL
            time = strftime(TIME_FORMAT_FILE_NAME, gmtime())
            file_name = f'{AVATAR_FOLDER}{user_id}/{time}.png'

            # delete all other previously used avatars for this user
            for obj in bucket.objects.filter(Prefix=f'{AVATAR_FOLDER}{user_id}/'):
                obj.delete()

            # upload
            result = bucket.upload_fileobj(
                io.BytesIO(file),
                file_name
            )

            url = USER_FILES_BUCKET_URL + file_name
        
            return ItemCrudResponse(
                Item={url},
                success=True,
                exception=None
            )
        
        except Exception as e:
            print('Error uploading avatar to S3: ', e)

            return ItemCrudResponse(
                Item={},
                success=False,
                exception=e
            )

    # return the default user avatar url
    def get_default_user_avatar_url(self):
        return DEFAULT_AVATAR_URL