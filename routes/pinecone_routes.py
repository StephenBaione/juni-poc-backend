from fastapi import APIRouter
from internal.handlers.pinecone_handlers import PineConeHandler
from data.pinecone.pinecone_index import PineConeIndex

pinecone_handler = PineConeHandler()

pinecone_router = APIRouter(prefix='/pinecone', tags=['Pinecone'])

@pinecone_router.post('/add_index_to_db')
async def add_index_to_db(pinecone_index: PineConeIndex):
    return pinecone_handler.handle_add_index_to_db(pinecone_index=pinecone_index)

