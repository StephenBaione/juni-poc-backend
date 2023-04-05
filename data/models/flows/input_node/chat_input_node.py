from .input_node import InputNode, InputNodeIOTypes

class ChatInputNode(InputNode):
    input_type = InputNodeIOTypes.CHAT_INPUT.value
    output_type = InputNodeIOTypes.CHAT_OUTPUT.value
