from .output_node import OutputNode, OutputtNodeIOTypes

class ChatOutputNode(OutputNode):
    _type = OutputtNodeIOTypes.CHAT.value
