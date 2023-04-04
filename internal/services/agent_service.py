from .dynamodb_service import DynamoDBService, ItemCrudResponse, Key

from data.models.agents.agent import Agent, AgentType, AgentSupportedService


class AgentService:
    def __init__(self) -> None:
        self.dynamodb_service = DynamoDBService('Agent')
        self.dynamodb_service_agent_type = DynamoDBService('AgentType')
        self.dynamodb_service_agent_supported_service = DynamoDBService('AgentSupportedService')
        self.dynamodb_service_available_agents = DynamoDBService('AvailableAgentsConfig')

    def create_agent(self, agent: Agent):
        agent = Agent.set_id(agent)
        agent = Agent.set_date_times(agent)

        return self.dynamodb_service.update_item(agent)
    
    def update_agent(self, owner: str, name: str, agent: Agent) -> ItemCrudResponse:
        result = self.get_agent(owner, name)

        if not result.success or result.Item == {}:
            return result
        
        agent = Agent.set_updated_at(agent)
        return self.dynamodb_service.update_item(agent)
    
    def list_agent(self, owner: str):
        id_keys = { 'owner': owner }

        return self.dynamodb_service.scan_table(None)
    
    def list_agent_names(self, owner: str):
        filter_expression = Key('owner').eq(owner)

        field_names = []
        reserved_keywords = {'owner': '#ow', 'name': '#na'}
        projection_expression, expression_attribute_names = DynamoDBService.generate_projection_expression(reserved_keywords=reserved_keywords, field_names=field_names)

        return self.dynamodb_service.scan_table(filter_expression=filter_expression, projection_expression=projection_expression, expression_attribute_names=expression_attribute_names)
    
    def get_agent(self, owner: str, name: str) -> ItemCrudResponse:
        id_keys = { 'owner': owner, 'name': name }

        return self.dynamodb_service.get_item(None, id_keys=id_keys)
    
    def delete_agent(self, owner: str, name: str) -> ItemCrudResponse:
        item_key = { 'owner': owner, 'name': name }

        return self.dynamodb_service.delete_item(None, item_key=item_key)

    def create_agent_type(self, agent_type: AgentType):
        agent_type = AgentType.set_id(agent_type)
        agent_type = AgentType.set_date_times(agent_type)

        return self.dynamodb_service_agent_type.update_item(agent_type)
    
    def get_agent_type(self, id: str, _type: str) -> ItemCrudResponse:
        id_keys = { 'id': id, 'type': _type }

        return self.dynamodb_service_agent_type.get_item(None, id_keys=id_keys)
    
    def delete_agent_type(self, id: str, _type: str) -> ItemCrudResponse:
        id_keys = { 'id': id, 'type': _type }

        return self.dynamodb_service_agent_type.delete_item(None, item_key=id_keys)
    

    def create_agent_supported_service(self, agent_supported_service: AgentSupportedService):
        agent_supported_service = AgentSupportedService.set_id(agent_supported_service)
        agent_supported_service = AgentSupportedService.set_date_times(agent_supported_service)

        return self.dynamodb_service_agent_supported_service.update_item(agent_supported_service)
    
    def get_agent_supported_service(self, service: str, id: str) -> AgentSupportedService:
        id_keys = { 'service': service, 'id': id }

        return self.dynamodb_service_agent_supported_service.get_item(None, id_keys=id_keys)
    
    def delete_agent_supported_service(self, service: str, id: str) -> AgentSupportedService:
        id_keys = { 'service': service, 'id': id }

        return self.dynamodb_service_agent_supported_service.delete_item(None, item_key=id_keys)
    
    def list_agent_supported_service(self, limit):
        return self.dynamodb_service_agent_supported_service.scan_table(None, limit)

    def get_available_agents_config(self, version: str):
        return self.dynamodb_service_available_agents.get_item(version)
