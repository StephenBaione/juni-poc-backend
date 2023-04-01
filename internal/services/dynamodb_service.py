from .boto3_service import Boto3Service, ResourceClients

from boto3.dynamodb.conditions import Key

import pydantic

from typing import Optional, Any

class ItemCrudResponse(pydantic.BaseModel):
    Item: dict
    success: bool
    exception: Optional[Any] = None

class GetItemBatchResponse(pydantic.BaseModel):
    Items: list
    success: bool
    exception: Optional[Any] = None

class DynamoDBService:
    _boto3_service = Boto3Service()
    _dynamodb_client = None
    _dynamodb_resource = None

    def __init__(self, table_name) -> None:
        DynamoDBService.set_dynamodb_client()
        DynamoDBService.set_dynamodb_resource()

        self.table_name = table_name
        self.table = DynamoDBService._dynamodb_resource.Table(table_name)
    
    @staticmethod
    def set_dynamodb_client():
        DynamoDBService._dynamodb_client = DynamoDBService._boto3_service.get_resource_client(ResourceClients.DYNAMODB)

    @staticmethod
    def set_dynamodb_resource():
        DynamoDBService._dynamodb_resource = DynamoDBService._boto3_service.get_resource(ResourceClients.DYNAMODB)

    def get_item(self, table_name: str, keys: dict) -> ItemCrudResponse:
        if DynamoDBService._dynamodb_client is None:
            self.set_dynamodb_client()
        
        try:
            result = DynamoDBService._dynamodb_client.get_item(
                TableName=table_name,
                Key=keys
            )

            if 'Item' in result:
                return ItemCrudResponse(Item=result['Item'], success=True)
            
            return ItemCrudResponse(Item={}, success=True)
        
        except Exception as e:
            return ItemCrudResponse(Item={}, success=False, exception=e)
    
    def update_item(self, item) -> ItemCrudResponse:
        try:
            table = self.table

            item_dict = dict(item)

            table.put_item(
                Item=item_dict
            )

            return ItemCrudResponse(
                Item=item_dict,
                success=True
            )

        except Exception as e:
            print(e)
            return ItemCrudResponse(
                Item={},
                success=False,
                exception=e
            )
