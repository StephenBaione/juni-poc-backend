from ..services.flow_service import FlowService

class FlowHandler:
    def __init__(self) -> None:
        self.flow_service = FlowService()

    def handle_get_availability_config(self, version: str):
        return self.flow_service.get_flow_availability_config(version)

