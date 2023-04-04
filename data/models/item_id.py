from uuid import uuid1, uuid4, getnode
from random import getrandbits


class ItemId:
    @staticmethod
    def generate_item_id(sequential=False) -> str:
        if not sequential:
            return str(uuid4)
        
        _node = getnode()
        _clock_seq = getrandbits(14)

        return str(uuid1(node=_node, clock_seq=_clock_seq))

