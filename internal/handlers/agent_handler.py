from ..services.agent_service import AgentService, ItemCrudResponse

from data.models.agents.agent import Agent, AgentSupportedService, AgentType

class AgentHandler:
    def __init__(self) -> None:
        self.agent_service = AgentService()

    def handle_create_agent(self, agent: Agent) -> Agent:
        return self.agent_service.create_agent(agent)
    
    def handle_update_agent(self, owner: str, name: str, agent: Agent) -> ItemCrudResponse:
        return self.agent_service.update_agent(owner, name, agent)
    
    def handle_get_agent(self, owner: str, name: str) -> Agent:
        return self.agent_service.get_agent(owner, name)
    
    def handle_delete_agent(self, owner: str, name: str) -> Agent:
        return self.agent_service.delete_agent(owner, name)
    
    def handle_list_agent(self, owner: str) -> Agent:
        response = self.agent_service.list_agent(owner)
        return response
    
    def handle_list_agent_names(self, owner: str) -> ItemCrudResponse:
        return self.agent_service.list_agent_names(owner)
    
    def handle_create_agent_type(self, agent_type: AgentType) -> AgentType:
        return self.agent_service.create_agent_type(agent_type)
    
    def handle_get_agent_type(self, id: str, _type: str) -> AgentType:
        return self.agent_service.get_agent_type(id, _type)
    
    def handle_delete_agent_type(self, id: str, _type: str) -> AgentType:
        return self.agent_service.delete_agent_type(id, _type)
    
    def handle_create_agent_supported_service(self, agent_supported_service: AgentSupportedService) -> AgentSupportedService:
        return self.agent_service.create_agent_supported_service(agent_supported_service)
    
    def handle_get_agent_supported_service(self, service: str, id: str) -> AgentSupportedService:
        return self.agent_service.get_agent_supported_service(service, id)
    
    def handle_delete_agent_supported_service(self, service, id):
        return self.agent_service.delete_agent_supported_service(service, id)
    
    def handle_list_agent_supported_service(self, limit):
        return self.agent_service.list_agent_supported_service(limit)
    
    def handle_get_available_agents_config(self, version: str):
        return self.agent_service.get_available_agents_config(version)