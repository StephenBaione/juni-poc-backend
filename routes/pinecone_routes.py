from fastapi import APIRouter
from internal.handlers.pinecone_handlers import PineConeHandler
from data.pinecone.pinecone_index import PineConeIndex

pinecone_handler = PineConeHandler()

pinecone_router = APIRouter(prefix='/pinecone', tags=['Pinecone'])

@pinecone_router.get('/index')
async def get_pinecone_index(index_id: str):
    return pinecone_handler.get_index(index_id)

@pinecone_router.get('/index/index_name')
async def get_pinecone_index_by_name(index_name: str):
    return pinecone_handler.get_index_by_name(index_name)

@pinecone_router.post('/index/add')
async def add_index_to_db(pinecone_index: PineConeIndex):
    return pinecone_handler.handle_add_index_to_db(pinecone_index=pinecone_index)

@pinecone_router.post('/index/update')
async def update_index_in_db(pinecone_index: PineConeIndex):
    return pinecone_handler.handle_update_index_in_db(pinecone_index)

@pinecone_router.delete('/index')
async def delete_index_from_db(pinecone_index_id: str):
    return pinecone_handler.delete_index_from_db(pinecone_index_id)

