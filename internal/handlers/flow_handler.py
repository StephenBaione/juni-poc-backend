from ..services.flow_service import FlowService

from pydantic import BaseModel

from typing import List, Any, Optional

class SaveFlowRequest(BaseModel):
    user_id: str
    nodes: List[Any]
    edges: List[Any]
    flow_id: Optional[str]

from uuid import uuid4

class FlowHandler:
    def __init__(self) -> None:
        self.flow_service = FlowService()

    def handle_get_availability_config(self, version: str):
        return self.flow_service.get_flow_availability_config(version)
    
    def handle_get_flow(self, flow_id: str):
        return self.flow_service.get_flow_template(flow_id)
    
    def handle_save_flow_template(self, nodes, edges, user_id, flow_id = None):
        # Build the flow
        flow_template = self.flow_service.flow_builder.build_flow(nodes, edges)

        # Save the new flow template
        if flow_id is None:
            flow_id = str(uuid4())

        flow_template['id'] = flow_id
        flow_template['user_id'] = user_id

        result = self.flow_service.save_flow_template(flow_template)

        return result
    
    def handle_list_user_flows(self, user_id: str):
        return self.flow_service.list_user_flows(user_id)

    def handle_get_flow_template(self, nodes, edges):
        pass

