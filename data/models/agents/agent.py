from pydantic import BaseModel

from typing import Optional

from enum import Enum

from uuid import uuid4

from datetime import datetime

class AgentType(BaseModel):
    id: Optional[str] = None
    service: str
    type: str
    input_type: str
    output_type: str
    created_at: Optional[str]
    updated_at: Optional[str]

    @staticmethod
    def set_id(agent: "AgentType") -> "AgentType":
        agent.id = str(uuid4())

        return agent

    @staticmethod
    def set_date_times(agent: "AgentType") -> "AgentType":
        agent.created_at = str(datetime.now())
        agent.updated_at = str(datetime.now())

        return agent
    
    @staticmethod
    def set_updated_at(agent: "AgentType") -> "AgentType":
        agent.updated_at = str(datetime.now())

        return agent

class AgentSupportedService(BaseModel):
    id: Optional[str] = None
    service: str
    created_at: Optional[str]
    updated_at: Optional[str]

    @staticmethod
    def set_id(agent: "AgentSupportedService") -> "AgentSupportedService":
        agent.id = str(uuid4())

        return agent

    @staticmethod
    def set_date_times(agent: "AgentSupportedService") -> "AgentSupportedService":
        agent.created_at = str(datetime.now())
        agent.updated_at = str(datetime.now())

        return agent
    
    @staticmethod
    def set_updated_at(agent: "AgentSupportedService") -> "AgentSupportedService":
        agent.updated_at = str(datetime.now())

        return agent

class AgentInputTypes(Enum):
    CHAT_MESSAGE: str
    CHAT_LIST: str

class Agent(BaseModel):
    id: Optional[str] = None
    name: str
    
    service: str
    type: str

    input_type: str
    output_type: str

    owner: str
    purpose: str
    created_at: Optional[str]
    updated_at: Optional[str]

    @staticmethod
    def from_json(agent_data) -> "Agent":
        return Agent(
            id = agent_data.get('id', None),
            name = agent_data['name'],
            service=agent_data['service'],
            type=agent_data['type'],
            input_type=agent_data['input_type'],
            output_type=agent_data['output_type'],
            owner=agent_data['owner'],
            purpose=agent_data['purpose'],
            created_at=agent_data.get('created_at', None),
            updated_at=agent_data.get('updated_at', None)
        )

    @staticmethod
    def set_id(agent: "Agent") -> "Agent":
        agent.id = str(uuid4())

        return agent

    @staticmethod
    def set_date_times(agent: "Agent") -> "Agent":
        agent.created_at = str(datetime.now())
        agent.updated_at = str(datetime.now())

        return agent
    
    @staticmethod
    def set_updated_at(agent: "Agent") -> "Agent":
        agent.updated_at = str(datetime.now())

        return agent
    
class AgentTypes(Enum):
    CHAT_GPT = 'chatgpt'
    SEMANTIC_SEARCH = 'semanticsearch'
    HISTORY = 'history'
    GPT4 = 'gpt4'
