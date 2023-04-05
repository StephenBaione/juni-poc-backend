from ..inputs.chat_input import ChatInput
from ..outputs.chat_output import ChatOutput

from ..agents.gpt_agent import GPTAgent

from data.models.conversation.chat_message import ChatMessage, ChatRoles

from queue import Queue

class Flow:
    def __init__(self, agent) -> None:
        self.output_queue = Queue()

        self.text_output = ChatOutput(self.output_queue)
        self.gpt_agent = GPTAgent(agent, self.text_output)
        self.text_input = ChatInput(self.gpt_agent)

    def start_flow(self):
        chat_message = ChatMessage(
            id='test',
            role=ChatRoles.USER_ROLE.value,
            sender='test',
            conversation_id='test',
            user='test',
            user_id='test',
            agent_name='test',
            message='Hello how are you doing today?'
        )

        return self.text_input.consume_input(chat_message)

if __name__ == '__main__':
    from data.models.agents.agent import Agent

    agent = Agent(
        id='test',
        name='agent',
        service='service',
        type='type',
        input_type='text',
        output_type='test',
        owner='test',
        purpose='stuff'
    )

    flow = Flow(agent=agent)
    output = flow.start_flow()
    print(output, flow.output_queue.get())

