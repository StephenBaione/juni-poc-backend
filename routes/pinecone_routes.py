from fastapi import APIRouter, File, UploadFile
from internal.handlers.pinecone_handlers import PineConeHandler
from data.pinecone.pinecone_index import PineConeIndex

from typing import Optional

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

@pinecone_router.post('/consume_pdf')
async def pinecone_consume_pdf(file: UploadFile, multicolumn: Optional[bool] = False):
    return await pinecone_handler.handle_consume_pdf(file, multicolumn)

@pinecone_router.post('/consume_pdf/langchain')
async def pinecone_consume_pdf_langchain(file_path: str):
    return pinecone_handler.pinecone_service.data_manager.chunk_pdf_langchain(file_path)

@pinecone_router.get('/search/plain_text')
async def pinecone_plain_text_search(index_name: str, namespace: str, plain_text: str):
    return pinecone_handler.plain_text_search(index_name=index_name, namespace=namespace, plain_text=plain_text)

@pinecone_router.delete('/namespace/all')
async def pinecone_delete_all_in_namespace(index_name: str, namespace: str):
    return pinecone_handler.delete_all_in_namespace(index_name, namespace)

