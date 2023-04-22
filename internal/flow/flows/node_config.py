from pydantic import BaseModel

from typing import Optional, List

from enum import Enum

class NodeConfig(BaseModel):
    Order: str
    SortedOrder: Optional[List[str]]

    @staticmethod
    def from_dict(data) -> "NodeConfig":
        node_config = NodeConfig(Order=data['Order'])

        if node_config.Order == SortTypes.SORTED_ORDER.value:
            node_config.SortedOrder = data['SortedOrder']

        return node_config

class SortTypes(Enum):
    FIRST_DONE = 'FirstDone'
    SORTED_ORDER = 'SortedOrder'
