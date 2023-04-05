from .input_node import InputNode, InputNodeIOTypes

class ChatInputNode(InputNode):
    input_type = InputNodeIOTypes.TEXT_INPUT.value
    output_type = InputNodeIOTypes.TEXT_OUTPUT.value
