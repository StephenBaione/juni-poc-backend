from .boto3_service import Boto3Service, ResourceClients

from boto3.dynamodb.conditions import Key

import pydantic

from typing import Optional, Any, List, Union

class ItemCrudResponse(pydantic.BaseModel):
    Item: Union[dict, List]
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

    def get_item(self, item_id: str) -> ItemCrudResponse:
        if DynamoDBService._dynamodb_client is None:
            self.set_dynamodb_client()
        
        try:
            result = self.table.get_item(
                Key={ 'id': item_id }
            )

            if 'Item' in result:
                return ItemCrudResponse(Item=result['Item'], success=True)
            
            return ItemCrudResponse(Item={}, success=True)
        
        except Exception as e:
            return ItemCrudResponse(Item={}, success=False, exception=e)
        
    def query_item(self, key_condition_expression):
        try:
            query = self.table.query(KeyConditionExpression=key_condition_expression)

            return ItemCrudResponse(
                Item=query['Items'],
                success=True,
                exception=e
            )

        except Exception as e:
            print(e)

            return ItemCrudResponse(
                Item={},
                success=False,
                exception=e
            )
        
    def scan_table(self, filter_expression, limit=None):
        try:
            results = []

            scan_args = {
                'FilterExpression': filter_expression
            }

            stop = False
            last_evaluated_key = None
            while not stop:
                response = self.table.scan(**scan_args)
                items = response.get('Items', [])

                if limit is not None:
                    if len(items) + len(results) > limit:
                        items = items[:limit - len(results)]

                results.extend(items)
                last_evaluated_key = response.get('LastEvaluatedKey', None)
                stop = last_evaluated_key is None \
                        or len(results) == limit
                
            return ItemCrudResponse(
                Item=results,
                success=True,
                exception=None
            )

        except Exception as e:
            print(e)

            return ItemCrudResponse(
                Item={},
                success=False,
                exception=e
            )
    
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
        
    def delete_item(self, item_id) -> ItemCrudResponse:
        try:
            self.table.delete_item(
                Key={'id': item_id}
            )

            return ItemCrudResponse(
                Item={},
                success=True,
                exception=None
            )

        except Exception as e:
            print(e)
            return ItemCrudResponse(
                Item={},
                success=False,
                exception=e
            )
