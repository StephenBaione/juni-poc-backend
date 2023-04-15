from fastapi import APIRouter, Body

from internal.handlers.flow_handler import FlowHandler, SaveFlowRequest, RunFlowRequest, FlowNameRequest

flow_handler = FlowHandler()
flow_router = APIRouter(prefix='/flow', tags=['Flow'])

@flow_router.get('/available_flows')
async def get_flow_availability_config(version: str):
    return flow_handler.handle_get_availability_config(version)

@flow_router.post('/save')
async def save_flow(save_flow_request: SaveFlowRequest = Body(...)):
    # If this is a new flow object, then it won't have an ID
    save_flow_request = dict(save_flow_request)
    flow_id = save_flow_request.get('flow_id', None)

    return flow_handler.handle_save_flow_template(save_flow_request['nodes'], save_flow_request['edges'], save_flow_request['user_id'], flow_id)

@flow_router.get('/get_flow/{flow_id}')
async def get_flow(flow_id: str):
    return flow_handler.handle_get_flow(flow_id)

@flow_router.delete('/delete_flow/{flow_id}')
async def delete_flow(flow_id: str):
    return flow_handler.handle_delete_flow(flow_id)

@flow_router.get('/user_flows/{user_id}')
async def list_user_flows(user_id: str):
    return flow_handler.handle_list_user_flows(user_id)

@flow_router.post('/run_flow/{flow_id}')
async def run_flow(run_flow_request: RunFlowRequest):
    return await flow_handler.handle_run_flow(run_flow_request.flow_id, run_flow_request.input_data)

@flow_router.post('/set_name/{flow_id}')
async def set_flow_name(flow_id: str, flow_name_request: FlowNameRequest = Body(...)):
    return flow_handler.handle_set_flow_name(flow_id, flow_name_request.flow_name)
