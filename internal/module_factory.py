from internal.services.pinecone_service import PineconeService
from internal.services.openai_service import OpenAIService

class ModuleFactory:
    service_map = {
        'pinecone': PineconeService,
        'openai': OpenAIService
    }

    @staticmethod
    def get_module_service(service_name):
        service_class = ModuleFactory.service_map.get(service_name, None)

        if service_class is None:
            raise ValueError(f'No service found for {service_name}')
        
        return service_class()

