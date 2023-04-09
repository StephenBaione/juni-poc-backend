from ..services.flow_service import FlowService

from pydantic import BaseModel

from typing import List, Any

class SaveFlowRequest(BaseModel):
    nodes: List[Any]
    edges: List[Any]

class FlowHandler:
    def __init__(self) -> None:
        self.flow_service = FlowService()

    def handle_get_availability_config(self, version: str):
        return self.flow_service.get_flow_availability_config(version)
    
    def handle_build_flow_template(self, nodes, edges):
        flow_template = self.flow_service.flow_builder.build_flow(nodes, edges)
        result = self.flow_service.save_flow_template(flow_template)

        return result

    def handle_get_flow_template(self, nodes, edges):
        pass

