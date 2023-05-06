import boto3

from botocore.config import Config

from dotenv import load_dotenv

import os

from enum import Enum

class ResourceClients(Enum):
    DYNAMODB = 'dynamodb',
    S3 = 's3'

class Boto3Service:
    def __init__(self) -> None:
        pass

    def get_resource_client(self, resource_client: ResourceClients):
        if resource_client == ResourceClients.DYNAMODB:
            return self.get_dynamodb_client()
        
        raise ValueError(f"Invalid resource client: {resource_client}")
    
    def get_resource(self, resource: ResourceClients, region_name: str = None):
        if resource == ResourceClients.DYNAMODB:
            return self.get_dynamodb_resource()
        
        if resource == ResourceClients.S3:
            return self.get_s3_resource(region_name)
        
        raise ValueError(f"Invalid resource: {resource}")
    
    def get_dynamodb_client(self):
        return boto3.client('dynamodb')
    
    def get_dynamodb_resource(self):
        return boto3.resource('dynamodb')
    
    def get_s3_resource(self, region_name: str):
        return boto3.resource('s3', region_name=region_name)




