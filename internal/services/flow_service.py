from internal.flow.flows.flow import Flow

from .dynamodb_service import DynamoDBService, ItemCrudResponse

class FlowService:
    def __init__(self) -> None:
        self.flow_table = DynamoDBService('Flow')
        self.flow_input_table = DynamoDBService('FlowInput')
        self.flow_output_table = DynamoDBService('FlowOutput')
        self.flow_config_table = DynamoDBService('FlowConfig')
        self.flow_availability_config_table = DynamoDBService('FlowAvailabilityConfig')

    def create_flow(flow_config):
        pass

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

    