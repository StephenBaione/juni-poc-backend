from fastapi import APIRouter, Body

from internal.handlers.agent_handler import AgentHandler

from data.models.agents.agent import Agent, AgentSupportedService, AgentType

agent_handler = AgentHandler()

agent_router = APIRouter(prefix='/agent', tags=['Agent'])

@agent_router.post('/create_agent')
async def create_agent(agent: Agent = Body(...)):
    return agent_handler.handle_create_agent(agent)

@agent_router.get('/available_agents')
async def get_available_agents_config(version: str):
    return agent_handler.handle_get_available_agents_config(version)

@agent_router.post('/{owner}/{name}/agent/update')
async def update_agent(owner: str, name: str, agent: Agent = Body(...)):
    return agent_handler.handle_update_agent(owner, name, agent)

@agent_router.get('/{owner}/agent/list')
async def list_agent(owner: str):
    return agent_handler.handle_list_agent(owner)

@agent_router.get('{owner}/agent/names/list')
async def list_agent_names(owner: str):
    return agent_handler.handle_list_agent_names(owner)

@agent_router.get('/{owner}/{name}/agent')
async def get_agent(owner: str, name: str):
    return agent_handler.handle_get_agent(owner, name)

@agent_router.delete('/{owner}/{name}/delete')
async def delete_agent(owner: str, name: str):
    return agent_handler.handle_delete_agent(owner, name)

@agent_router.post('/type')
async def create_agent_type(agent_type: AgentType = Body(...)):
    return agent_handler.handle_create_agent_type(agent_type)

@agent_router.get('/{id}/{_type}/type')
async def get_agent_type(id: str, _type: str):
    return agent_handler.handle_get_agent_type(id, _type)

@agent_router.delete('/type/{id}/{_type}/delete')
async def delete_agent_type(id: str, _type: str):
    return agent_handler.handle_delete_agent_type(id, _type)

@agent_router.post('/service')
async def create_agent_supported_service(_agent_service: AgentSupportedService = Body(...)):
    return agent_handler.handle_create_agent_supported_service(_agent_service)

@agent_router.get('/service/list')
async def list_agent_supported_service(limit: int = 20):
    return agent_handler.handle_list_agent_supported_service(limit)

@agent_router.get('/{service}/{id}/service')
async def get_agent_supported_service(service: str, id: str):
    return agent_handler.handle_get_agent_supported_service(service, id)


@agent_router.delete('/service/{service}/{id}/delete')
async def delete_agent_supported_service(service: str, id: str):
    return agent_handler.handle_delete_agent_supported_service(service, id)
