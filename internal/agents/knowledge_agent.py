from internal.services.pinecone_service import PineconeService, ItemCrudResponse

from .base_agent import BaseAgent

from data.models.agents.agent import Agent

class KnowledgeAgent(BaseAgent):
    def __init__(self, agent: Agent, consumer: BaseAgent, producer: BaseAgent) -> None:
        super().__init__(agent, consumer, producer)

        self.index = ''
        self.namespace = ''
        self.text = ''

        self.pinecone_service = PineconeService()

    def set_index(self, index: str):
        self.pinecone_service.load_index(index)
        self.index = index

    def set_namespace(self, namespace: str):
        self.namespace = namespace

    def consume_input(self, text: str):
        self.text = text

    def execute(self) -> ItemCrudResponse:
        response = self.pinecone_service.plain_text_query(self.index, self.namespace, self.text)

        if self.consumer is not None:
            return self.chain_consumers(response)
        
        return response

