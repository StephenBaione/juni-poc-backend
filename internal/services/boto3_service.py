import boto3

from botocore.config import Config

from dotenv import load_dotenv

import os

from enum import Enum

class ResourceClients(Enum):
    DYNAMODB = 'dynamodb'

class Boto3Service:
    def __init__(self) -> None:
        pass

    def get_resource_client(self, resource_client: ResourceClients):
        if resource_client == ResourceClients.DYNAMODB:
            return self.get_dynamodb_client()
        
        raise ValueError(f"Invalid resource client: {resource_client}")
    
    def get_resource(self, resource: ResourceClients):
        if resource == ResourceClients.DYNAMODB:
            return self.get_dynamodb_resource()
        
        raise ValueError(f"Invalid resource: {resource}")
    
    def get_dynamodb_client(self):
        return boto3.client('dynamodb')
    
    def get_dynamodb_resource(self):
        return boto3.resource('dynamodb')




