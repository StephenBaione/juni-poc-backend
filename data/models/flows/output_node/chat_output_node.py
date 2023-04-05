from .output_node import Out, InputNodeIOTypes

class ChatInputNode(InputNode):
    input_type = InputNodeIOTypes.CHAT_INPUT.value
    output_type = InputNodeIOTypes.CHAT_OUTPUT.value
