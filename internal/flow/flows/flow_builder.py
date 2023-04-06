from pydantic import BaseModel

from enum import Enum

from ..inputs.chat_input import ChatInput
from ..outputs.chat_output import ChatOutput

from data.models.conversation.chat_message import ChatMessage, ChatRoles

from ..agents.gpt_agent import GPTAgent
from ..agents.knowledge_agent import KnowledgeAgent

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

# As a first test case, we'll manually run it
class FlowRunner:
    def __init__(self) -> None:
        self.chat_output = ChatOutput()

        self.gpt_agent = GPTAgent(None, self.chat_output)
        self.knowledge_agent = KnowledgeAgent(None, self.gpt_agent, 'medical-documents', 'medical-docs')
        # Add a history agent,
        # Set arbitrary max token size,
        # Run a scan in dynamodb for chat message in conversation

        self.chat_input = ChatInput(self.knowledge_agent)

    def execute(self):
        chat_message = ChatMessage(
            conversation_id = "c1bc4ed6-d608-4a20-8262-f79c2c4ed8f6ng",
            id = "test",
            agent_name = "Combat AiD",
            created_at = "2023-04-03 20:37:07.688239",
            message = "How do I fix a broken ankle?",
            role = ChatRoles.USER_ROLE.value,
            sender = "stephenbaione",
            updated_at = "2023-04-03 20:37:07.688239",
            user = "stephenbaione",
            user_id = "54c54359-3f55-4c5c-bb15-fb6457bec214"
        )
        response, response_dict = self.chat_input.consume_input(chat_message)
        print(response)

        from pprint import pprint
        pprint(response_dict)

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

    def temp_validation(self, flow_template):
        flow_template = {'0': {'Agent': {'created_at': None,
                     'id': 'test_id',
                     'input_type': 'text',
                     'name': 'History Agent',
                     'output_type': 'text',
                     'owner': '54c54359-3f55-4c5c-bb15-fb6457bec214',
                     'purpose': 'Chat History',
                     'service': 'pinecone',
                     'type': 'PineconeService',
                     'updated_at': '2023-04-04 14:58:34.463976'},
           'Consumers': ['2'],
           'Type': 'agent'},
        '1': {'Agent': {'created_at': '2023-04-03 23:15:36.566887',
                        'id': '37ee5199-7472-4e4c-ac12-7201927fed5a',
                        'input_type': 'text',
                        'name': 'Knowledge Agent',
                        'output_type': 'text',
                        'owner': '54c54359-3f55-4c5c-bb15-fb6457bec214',
                        'purpose': 'Chat Knowledge',
                        'service': 'pinecone',
                        'type': 'PineconeService',
                        'updated_at': '2023-04-03 23:15:36.566894'},
            'Consumers': ['2'],
            'Type': 'agent'},
        '2': {'Agent': {'created_at': '2023-04-03 23:14:30.867621',
                        'id': '369800bb-c551-4301-b218-3ef37f6f76d9',
                        'input_type': 'text',
                        'name': 'GPT Agent',
                        'output_type': 'text',
                        'owner': '54c54359-3f55-4c5c-bb15-fb6457bec214',
                        'purpose': 'Chat Completion',
                        'service': 'openai',
                        'type': 'ChatGPT',
                        'updated_at': '2023-04-03 23:14:30.867641'},
            'Consumers': ['4'],
            'Type': 'agent'},
        '3': {'Consumers': ['0', '1'], 'InputType': 'ChatInput', 'Type': 'input'},
        '4': {'Consumers': [], 'OutputType': 'ChatOutput', 'Type': 'output'},
        'Input': '3',
        'Output': '4'}
        
        # save the input node
        input_node_key = flow_template["Input"]
        output_node_key = flow_template["Output"]

        # remove the input and output key
        flow_template.pop("Input")
        flow_template.pop("Output")


        # TODO: Revisit flow, like one input, one output, and one agent
        def is_valid_graph(flow_template, input_node_key, output_node_key):
            # Validate the flow
            visited = set()

            def validate_node(node_key: str) -> bool:
                consumers = flow_template[node_key]['Consumers']

                # If no consumers, it should be the output node
                if len(consumers) == 0:
                    if node_key != output_node_key:
                        return False
                    
                    return True
                    
                # Output nodes should have no consumers
                if node_key == output_node_key:
                    return False
                    
                for consumer in consumers:
                    # Self looping node
                    if consumer == node_key:
                        return False

                    node = flow_template[node_key]

                    # Input cannot connect to output
                    if node_key == input_node_key:
                        if consumer == output_node_key:
                            return False
                        
                    # Agent checks
                    elif node['Type'] == 'agent':
                        # Can only be agent or output
                        if consumer == input_node_key:
                            return False

                return True

            def dfs(node_key):
                visited.add(node_key)
                print(visited)
                if not validate_node(node_key):
                    return False

                node = flow_template[node_key]
                consumers = node['Consumers']
                
                if len(consumers) == 0:
                    if node_key != output_node_key:
                        return False

                print(node['Consumers'])
                for consumer in node["Consumers"]:
                    if consumer not in visited:
                        # print(visited)
                        if not dfs(consumer):
                            return False

                return True

            return dfs(input_node_key)

        result = is_valid_graph(flow_template, input_node_key, output_node_key)

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


