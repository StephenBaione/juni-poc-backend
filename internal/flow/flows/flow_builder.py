from pydantic import BaseModel

from enum import Enum

from ..inputs.chat_input import ChatInput
from ..outputs.chat_output import ChatOutput

from data.models.conversation.chat_message import ChatMessage, ChatRoles
from data.models.agents.agent import AgentTypes, Agent

from ..agents.gpt_agent import GPTAgent
from ..agents.semantic_search_agent import SemanticSearchAgent
from ..agents.history_agent import HistoryAgent

from ..connections.sequential_connection import SequentialConnection, ConnectionInput

from typing import List, Any

import asyncio
from asyncio import Event

from queue import Queue

from collections import deque

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

class FlowTemplate(BaseModel):
    Input: str
    Output: str

    nodes: Any
    edges: Any

    template: Any

# As a first test case, we'll manually run it
class FlowRunner:
    def __init__(self) -> None:
        self.chat_output = ChatOutput()

        self.gpt_agent = GPTAgent(None, self.chat_output)
        self.knowledge_agent = SemanticSearchAgent(None, self.gpt_agent, 'medical-documents', 'medical-docs')
        
        # Add a history agent,
        # Set arbitrary max token size,
        # Run a scan in dynamodb for chat message in conversation
        self.history_agent = HistoryAgent(None, self.knowledge_agent)

        #self.chat_input = ChatInput(self.knowledge_agent)
        self.chat_input = ChatInput(self.history_agent)

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
    def build_flow_template(self, flow_template):
        # Grab input and output
        input_key = flow_template['Input']
        input_node = flow_template[input_key]

        output_key = flow_template['Output']
        output_node = flow_template[output_key]

        nodes = flow_template['Nodes']

    def node_obj_from_type(self, node, connection):
        node_type = node['Type']

        node_obj = None
        if node_type == 'input':
            node_obj = ChatInput()
            node_obj.set_connection(connection)

        elif node_type == 'output':
            node_obj = ChatOutput()
            node_obj.set_connection(connection)

        elif node_type == 'agent':
            agent = Agent.from_json(node['Agent'])
            print(agent.type, AgentTypes.SEMANTICSEARCH.value)

            if agent.type.lower() == AgentTypes.CHAT_GPT.value:
                node_obj = GPTAgent(agent, connection)
            
            elif agent.type.lower() == AgentTypes.SEMANTICSEARCH.value:
                node_obj = SemanticSearchAgent(agent, connection)

            elif agent.type.lower() == AgentTypes.HISTORY.value:
                node_obj = HistoryAgent(agent, connection)

        return node_obj

    def create_node_connection(self, flow_template, node, node_key):
        # We are going to create a connection for the two agents,
        # then create the producer and consumer and add to connection
        
        # First, create the connection between the nodes
        connection_input = ConnectionInput.get_instance()
        connection = SequentialConnection(connection_input)

        producer_obj = self.node_obj_from_type(node, connection)
        # Set the producer object
        connection.set_producer_agent(producer_obj)

        if node_key == flow_template['Output']:
            return None

        consumer_node_keys = node['Consumers']
        for consumer_node_key in consumer_node_keys:
            consumer_node = flow_template[consumer_node_key]
            consumer_obj = self.node_obj_from_type(consumer_node, connection)
            connection.add_consumer_agent(consumer_obj)

        
        return {
            "Connection": connection,
            "Producer": producer_obj,
            "Consumer": consumer_obj,
            "ProducerNodeKey": node_key,
            "ConsumerNodeKeys": consumer_node_keys
        }

    async def execute_flow(
        self,
        input_node_key,
        flow_template,
        input_data
    ):
        """Perform a bredth first search on the flow template,
        to traverse and execute each node.

        To do this, we are going to 

        Args:
            input_node_key (_type_): _description_
            flow_template (_type_): _description_
        """
        visisted = set()

        input_node = flow_template[input_node_key]
        queue = deque([input_node_key])

        agent_input_map = {}

        outputnode_key = None
        results = []
        while queue:
            node_key = queue.popleft()
            node = flow_template[node_key]

            if node_key not in visisted:
                visisted.add(node_key)

                result = \
                    self.create_node_connection(flow_template, node, node_key)
                
                if result is not None:
                    results.append(result)

                    for consumer_node_key in result['ConsumerNodeKeys']:
                        queue.append(consumer_node_key)

        agent_input_map[input_node_key] = input_data
        for result in results:
            producer = result['Producer']

            producer_key = result['ProducerNodeKey']
            producer_input = agent_input_map[producer_key]
            output = await producer.consume(producer_input)

            for consumer_key in result['ConsumerNodeKeys']:
                if agent_input_map.get(consumer_key, None) is None:
                    agent_input_map[consumer_key] = []

                if isinstance(output, list):
                    agent_input_map[consumer_key].extend(output)
                else:
                    agent_input_map[consumer_key].append(output)

        return results



    def dfs(
        self,
        node_key,
        flow_template,
        input_node,
        visited,
        output_node_key,
        callback
    ):
        visited.add(node_key)

        node = flow_template[node_key]

        # First, we have to create the connection between the nodes,
        # Then, we're going to set the consumer and producer for the connection,
        # Then we're going to continue on to the next edge

        
        # If we've reached the end of the graph,
        # return the input node, now that all of the connections
        # and consumers have been set.
        if len(consumers) == 0:
            return input_node

        # First, create connection events. These allow the agents to communicate
        # with the connection node
        on_start = Event()
        on_output = Event()
        input_queue = Queue()
        response_dict = {}

        connection_input = ConnectionInput(
            on_start=on_start,
            on_output=on_output,
            input_queue=input_queue,
            response_dict=response_dict
        )

        sequential_connection = SequentialConnection(connection_input)
        sequential_connection.set_producer_agent(agent)

        consumers = node['Consumers']
        for consumer in node["Consumers"]:
            agent = flow_template[consumer]['Agent']
            agent = Agent.from_json(agent)

            flow_agent = None
            if agent.type == AgentTypes.CHAT_GPT.value:
                flow_agent = GPTAgent(agent, sequential_connection)
            
            if flow_agent is None:
                raise NotImplementedError(f"{agent.type} is not a supported agent type.")
            
            sequential_connection.add_consumer_agent(GPTAgent)


            if consumer not in visited:
                # print(visited)
                return self.df

        return True


    def temp_validation(self, flow_template):
        # flow_template = {
        #     "Nodes": {
        #         '0': {
        #             'Agent': {
        #                 'created_at': None,
        #                 'id': 'test_id',
        #                 'input_type': 'text',
        #                 'name': 'History Agent',
        #                 'output_type': 'text',
        #                 'owner': '54c54359-3f55-4c5c-bb15-fb6457bec214',
        #                 'purpose': 'Chat History',
        #                 'service': 'pinecone',
        #                 'type': 'PineconeService',
        #                 'updated_at': '2023-04-04 14:58:34.463976'
        #             },
        #             'Consumers': ['2'],
        #             'Type': 'agent'
        #         },
        #         '1': {
        #             'Agent': {
        #                 'created_at': '2023-04-03 23:15:36.566887',
        #                 'id': '37ee5199-7472-4e4c-ac12-7201927fed5a',
        #                 'input_type': 'text',
        #                 'name': 'Knowledge Agent',
        #                 'output_type': 'text',
        #                 'owner': '54c54359-3f55-4c5c-bb15-fb6457bec214',
        #                 'purpose': 'Chat Knowledge',
        #                 'service': 'pinecone',
        #                 'type': 'PineconeService',
        #                 'updated_at': '2023-04-03 23:15:36.566894'
        #             },
        #             'Consumers': ['4'],
        #             'Type': 'agent'
        #         },
        #         '2': {
        #             'Agent': {
        #                 'created_at': '2023-04-03 23:14:30.867621',
        #                 'id': '369800bb-c551-4301-b218-3ef37f6f76d9',
        #                 'input_type': 'text',
        #                 'name': 'GPT Agent',
        #                 'output_type': 'text',
        #                 'owner': '54c54359-3f55-4c5c-bb15-fb6457bec214',
        #                 'purpose': 'Chat Completion',
        #                 'service': 'openai',
        #                 'type': 'ChatGPT',
        #                 'updated_at': '2023-04-03 23:14:30.867641'
        #             },
        #             'Consumers': ['1'],
        #             'Type': 'agent'
        #         },
        #         '3': {
        #             'Consumers': ['0'],
        #             'InputType': 'ChatInput',
        #             'Type': 'input'
        #         },
        #         '4': {
        #             'Consumers': [],
        #             'OutputType': 'ChatOutput',
        #             'Type': 'output'
        #         }
        #     },
        #     'Input': '3',
        #     'Output': '4'
        # }
        
        # save the input node
        input_node_key = flow_template["Input"]
        output_node_key = flow_template["Output"]


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
            "Output": "",
            "Nodes": nodes,
            "Edges": edges,
            "Template": {}
        }

        for node in nodes:
            node_id = node['id']

            node_data = node['data']
            if node_data['type'] == NodeTypes.INPUT_TYPE.value:
                flow_template['Input'] = node_id
                input_type = node_data['label']

                flow_template["Template"][node_id] = {
                    "Type": NodeTypes.INPUT_TYPE.value,
                    "InputType": input_type,
                    "Consumers": []
                }

            elif node_data['type'] == NodeTypes.OUTPUT_TYPE.value:
                flow_template['Output'] = node_id

                ouput_type = node_data['label']

                flow_template["Template"][node_id] = {
                    "Type": NodeTypes.OUTPUT_TYPE.value,
                    "OutputType": ouput_type,
                    "Consumers": []
                }

            else:
                agent = node_data['agent']
                flow_template["Template"][node_id] = {
                    'Type': NodeTypes.AGENT_TYPE.value,
                    'Agent': agent,
                    'Consumers': []
                }

        for edge in edges:
            source_id = edge['source']
            target_id = edge['target']

            source_node = flow_template["Template"][source_id]

            source_node['Consumers'].append(
                target_id
            )

        return flow_template


