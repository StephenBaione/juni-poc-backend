from pydantic import BaseModel

from enum import Enum

from ..inputs.chat_input import ChatInput
from ..outputs.chat_output import ChatOutput

from typing import List

class Node(BaseModel):
    id: str

    # Label and type
    data: dict
    type: str

class NodeTypes(Enum):
    INPUT_TYPE = 'input'
    OUTPUT_TYPE = 'output'
    AGENT_TYPE = 'agent'

class Edge(BaseModel):
    source: str
    target: str


class FlowBuilder:
    def __init__(self) -> None:
        pass


    # Find input - tells us where to start
    # Find output - Tells us when we're done

    # Start With Input node
    # Write the template definition for input

    # Find agents for input node
    # Write agent definitions
    
    # For each agent, find connected node, write definition

    # Write output node definition
    def build_flow(self, nodes: List[Node], edges: List[Edge]):
        flow_template = {
            "Input": "",
            "Output": ""
        }

        for node in nodes:
            node_id = node['id']

            node_data = node['data']
            if node_data['type'] == NodeTypes.INPUT_TYPE.value:
                flow_template['Input'] = node_id
                input_type = node_data['label']

                flow_template[node_id] = {
                    "Type": NodeTypes.INPUT_TYPE.value,
                    "InputType": input_type,
                    "Consumers": []
                }

            elif node_data['type'] == NodeTypes.OUTPUT_TYPE.value:
                flow_template['Output'] = node_id

                ouput_type = node_data['label']

                flow_template[node_id] = {
                    "Type": NodeTypes.OUTPUT_TYPE.value,
                    "OutputType": ouput_type,
                    "Consumers": []
                }

            else:
                agent = node_data['agent']
                flow_template[node_id] = {
                    'Type': NodeTypes.AGENT_TYPE.value,
                    'Agent': agent,
                    'Consumers': []
                }

        for edge in edges:
            source_id = edge['source']
            target_id = edge['target']

            source_node = flow_template[source_id]

            source_node['Consumers'].append(
                target_id
            )

        return flow_template
                

