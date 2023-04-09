from internal.flow.flows.flow import Flow
from internal.flow.flows.flow_builder import FlowBuilder

from .dynamodb_service import DynamoDBService, ItemCrudResponse

from uuid import uuid4

class FlowService:
    def __init__(self) -> None:
        self.flow_table = DynamoDBService('Flow')
        self.flow_input_table = DynamoDBService('FlowInput')
        self.flow_output_table = DynamoDBService('FlowOutput')
        self.flow_config_table = DynamoDBService('FlowConfig')
        self.flow_availability_config_table = DynamoDBService('FlowAvailabilityConfig')
        self.flow_template_table = DynamoDBService('FlowTemplate')

        self.flow_builder = FlowBuilder()

    def create_flow(self, nodes, edges):
        return self.flow_builder.build_flow(nodes, edges)

    def get_flow_availability_config(self, version: str) -> ItemCrudResponse:
        try:
            query_key = { 'version': version }

            return self.flow_availability_config_table.get_item(None, id_keys=query_key)

        except Exception as e:
            print(e)

            return ItemCrudResponse(
                Item={},
                success=False,
                exception=e
            )

    def update_flow_availability_config(self, flow_availability_config: dict) -> ItemCrudResponse:
        try:
            return self.flow_availability_config_table.update_item(flow_availability_config)

        except Exception as e:
            print(e)

            return ItemCrudResponse(
                Item={},
                success=False,
                exception=e
            )
        
    def save_flow_template(self, flow_template) -> ItemCrudResponse:
        try:
            _id = flow_template.get('id', None)

            if _id is None:
                flow_template['id'] = str(uuid4())

            return self.flow_template_table.update_item(flow_template)

        except Exception as e:
            return ItemCrudResponse(
                Item={},
                success=False,
                exception=e
            )
        
    def get_flow_template(self, flow_id) -> ItemCrudResponse:
        try:
            id_key = { 'id': flow_id }
            return self.flow_template_table.get_item(None, id_keys=id_key)

        except Exception as e:
            return ItemCrudResponse(
                Item={},
                success=False,
                exception=e
            )

    