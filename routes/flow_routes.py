from fastapi import APIRouter, Body

from internal.handlers.flow_handler import FlowHandler

flow_handler = FlowHandler()
flow_router = APIRouter(prefix='/flow', tags=['Flow'])

@flow_router.get('/available_flows')
async def get_flow_availability_config(version: str):
    return flow_handler.handle_get_availability_config(version)

@flow_router.post('/build')
async def build_flow(nodes):
    pass
