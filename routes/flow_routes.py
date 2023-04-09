from fastapi import APIRouter, Body

from internal.handlers.flow_handler import FlowHandler, SaveFlowRequest

flow_handler = FlowHandler()
flow_router = APIRouter(prefix='/flow', tags=['Flow'])

@flow_router.get('/available_flows')
async def get_flow_availability_config(version: str):
    return flow_handler.handle_get_availability_config(version)

@flow_router.post('/save')
async def save_flow(save_flow_request: SaveFlowRequest = Body(...)):
    return flow_handler.handle_build_flow_template(save_flow_request.nodes, save_flow_request.edges)

# @flow_router.get('/run')
# async def run_flow(flow_id: str):
#     return flow_handler
