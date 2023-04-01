from dotenv import load_dotenv
load_dotenv()

import os
import itertools

from io import BytesIO

import pydantic
import typing
from uuid import uuid4

import pinecone

from data.data_manager import DataManager, PDFFile

from .openai_service import OpenAIClient

from .dynamodb_service import DynamoDBService, ItemCrudResponse, Key

from enum import Enum

class MetaDataConfig(pydantic.BaseModel):
    indexed: typing.List[str]

    def __init__(self, indexed: typing.List[str]) -> None:
        self.indexed = indexed

class MetaDataFilter(pydantic.BaseModel):
    metadata_items = []

class PineConeNameSpaces(Enum):
    MEDICAL_DOCS = 'medical-docs'

class PineConeIndexes(Enum):
    MEDICAL_DOCS = 'medical-documents'

class MedicalMetaData(pydantic.BaseModel):
    Filename: str
    PageNumber: int
    ParagraphNumber: int

class PineConeItem(pydantic.BaseModel):
    id: str
    vector: typing.List[float]
    metadata: typing.Dict[str, typing.Any]
    namespace: str

    def __init__(__pydantic_self__, **data: typing.Any) -> None:
        if data.get('id', None) is None:
            data['id'] = str(uuid4())

        super().__init__(**data)

    def __iter__(self) -> typing.Generator:
        yield 'id', self.id
        yield 'vector', self.vector
        yield 'metadata', self.metadata
        yield 'namespace', self.namespace

    @staticmethod
    def from_pinecone_item(item: 'PineConeItem') -> 'PineConeItem':
        return PineConeItem(
            id=item.id,
            vector=item.vector,
            metadata=item.metadata,
            namespace=item.namespace
        )

    @staticmethod
    def to_dict(item: 'PineConeItem'):
        return {
            'id': item.id,
            'vector': item.vector,
            'metadata': item.metadata,
            'namespace': item.namespace
        }

    @staticmethod
    def upsert_tuple(item: 'PineConeItem'):
        return item.id, item.vector, item.metadata

class PineConeIndex(pydantic.BaseModel):
    index_name: str
    environment_name: os.getenv('PINECONE_ENVIRONMENT')
    dimensions: int
    pod_type: str
    pods_per_replica: str
    replicas: str
    total_pods: str
    metric: str = 'cosine'

class PineconeService:
    index_map = {}

    def __init__(self) -> None:
        self.pine_cone_api_key = os.getenv('PINECONE_API_KEY')
        self.pine_cone_environment = os.getenv('PINECONE_ENVIRONMENT')
        self.pine_cone_index_name = os.getenv('PINECONE_INDEX_NAME')

        pinecone.init(api_key=self.pine_cone_api_key, environment=self.pine_cone_environment)
        
        self.data_manager = DataManager()
        
        self.dynamodb_service = DynamoDBService('pinecone-index')
        self.openai_service = OpenAIClient()

    @staticmethod
    def create_index(name: str, dimension: int, metadata_config=MetaDataConfig):
        return pinecone.create_index(name=name, dimension=dimension,
                              metadata_config=metadata_config)
    
    def get_index(self, index_id: str):
        return self.dynamodb_service.get_item(index_id)
    
    def get_index_by_name(self, index_name: str):
        filter_expression = Key('index_name').eq(index_name)

        return self.dynamodb_service.scan_table(filter_expression, limit=1)

    def save_index_to_db(self, index: PineConeIndex):
        dynamodb_service = self.dynamodb_service

        return dynamodb_service.update_item(index)
    
    def delete_index_from_db(self, item_id: str) -> ItemCrudResponse:
        return self.dynamodb_service.delete_item(item_id)
    
    def update_index_in_db(self, index: PineConeIndex):
        item_id = index.id

        get_response = self.dynamodb_service.get_item(item_id)

        # If item is empty, or not successful, return crud response
        if not get_response.success or not get_response.Item:
            return get_response
        
        return self.dynamodb_service.update_item(index)
    
    def consume_pdf(self, pdf_file_name: str, pdf_file_bytes: BytesIO):
        pdf_file = DataManager.generate_pdf_file_from_name_bytes(
            pdf_file_name,
            pdf_file_bytes
        )

        parse_results, chunks = self.data_manager.chunk_pdf(pdf_file, save_chunks=True)
        return self.create_medical_doc_indexes(pdf_file_name, parse_results, chunks)

    def create_medical_doc_indexes(self, pdf_file_name, parse_results: dict, chunks: list):
        name_space = PineConeNameSpaces.MEDICAL_DOCS.value

        pinecone_items = []
        openai_service = self.openai_service

        on_chunk = lambda chunk_batch: openai_service.get_embeddings_batch_with_retry(chunk_batch)
        
        embeddings_unpacked = []
        embeddings = PineconeService.upsert_chunk_generator(
            chunks, 100, on_chunk=on_chunk
        )

        for embedding in embeddings:
            embeddings_unpacked.extend(embedding)
        
        # Create pinecone items, whose embedding will be filled in later
        item_count = 0
        for (page_number, paragraph_number), chunk in parse_results.items():
            # Define metadata for index
            metadata = MedicalMetaData(Filename=pdf_file_name, PageNumber=page_number, ParagraphNumber=paragraph_number)
            
            # Collect default values for pinecone_items
            pinecone_items.append(
                PineConeItem(**{
                    'vector': embeddings_unpacked[item_count],
                    'metadata': dict(metadata),
                    'namespace': name_space
                })
            )

        PineconeService.upsert_large_batch(
            PineConeIndexes.MEDICAL_DOCS.value,
            pinecone_items,
            namespace=name_space
        )

        return ItemCrudResponse(
            Item={
                'item_count': item_count,
                'file_name': pdf_file_name
            },
            success=True,
            exception=None
        )

    def plain_text_query(self, index_name, namespace, plain_text, top_k=5):
        # Load pinecone index
        index = PineconeService.load_index(index_name)
        
        # Get embeddings from text
        text_embeddings = self.openai_service.get_embeddings(plain_text)

        # Query pinecone database in namespace, for semantic similarity
        top_k_vectors = index.query(
            vector=text_embeddings,
            namespace=namespace,
            top_k=5
        )

        return top_k_vectors

    @staticmethod
    def delete_index(name: str):
        return pinecone.delete_index(name=name)

    @staticmethod
    def list_indexes():
        return pinecone.list_indexes()

    @staticmethod
    def describe_index(name: str):
        return pinecone.describe_index(name=name)

    @staticmethod
    def load_index(name: str) -> pinecone.Index:
        index = PineconeService.index_map.get(name, None)

        if index is not None:
            return index

        index = pinecone.Index(index_name=name)
        PineconeService.index_map[name] = index

        return index

    @staticmethod
    def upsert_data(index_name, data: PineConeItem):
        index = PineconeService.load_index(index_name)
        return index.upsert(
            PineconeService.upsert_tuple(data),
            namespace=data.namespace
        )

    @staticmethod
    def upsert_small_batch(index_name, data: typing.List[PineConeItem], namespace: str = 'default'):
        if len(data) > 100:
            raise ValueError('Batch size must be less than 100.')

        index = PineconeService.load_index(index_name)
        upsert_data = [PineconeService.upsert_tuple(item) for item in data]
        return index.upsert(
            upsert_data,
            namespace=namespace
        )

    @staticmethod
    def upsert_chunk_generator(iterable, batch_size = 100, on_chunk: typing.Callable = None):
        """A helper function to break an iterable into chunks of size batch_size."""
        it = iter(iterable)
        chunk = tuple(itertools.islice(it, batch_size))
        while chunk:
            if on_chunk is not None:
                yield on_chunk(chunk)
            else:
                yield chunk
            chunk = tuple(itertools.islice(it, batch_size))

    @staticmethod
    def upsert_large_batch(index_name, data: typing.List[PineConeItem], tqdm: typing.Callable = None, namespace: str = 'default'):
        index = PineconeService.load_index(index_name)

        if tqdm is not None:
            for upsert_data in tqdm(PineconeService.upsert_chunk_generator(
                data,
                batch_size = 100, 
                on_chunk = lambda chunk_list: [
                    chunk for chunk in map(lambda item: PineConeItem.upsert_tuple(item), chunk_list)
                ]
            )):
                index.upsert(
                    upsert_data,
                    namespace=namespace
                )
            return

        for upsert_data in PineconeService.upsert_chunk_generator(
            data, 
            batch_size = 100, 
            on_chunk = lambda chunk_list: [
                chunk for chunk in map(lambda item: PineConeItem.upsert_tuple(item), chunk_list)
            ]
        ):
            index.upsert(
                upsert_data,
                namespace=namespace
            )

    @staticmethod
    def fetch_vector_list(index_name, ids: typing.List[str]):
        index = PineconeService.load_index(index_name)
        return index.fetch(ids)

    @staticmethod
    def fetch_vector(index_name, id: str):
        index = PineconeService.load_index(index_name)
        return index.fetch([id])

    @staticmethod
    def _update_item(index: pinecone.Index, id: str, vector: typing.List[float] = None, metadata: typing.Dict[str, typing.Any] = None):
        if vector is not None:
            if metadata is not None:
                return index.update(
                    id=id,
                    values=vector,
                    set_metadata=metadata
                )

            return index.update(
                id=id,
                values=vector
            )

        elif metadata is not None:
            return index.update(
                id=id,
                set_metadata=metadata
            )

        else:
            raise ValueError('Either vector or metadata must be provided.')

    @staticmethod
    def update_item(index_name, values = None, metadata = None):
        index = PineconeService.load_index(index_name)
        return PineconeService._update_item(index, values, metadata)

    @staticmethod
    def delete_item(index_name, ids: typing.List[str]):
        index = PineconeService.load_index(index_name)
        return index.delete(ids)

    @staticmethod
    def search(index_name, query_vector: list, top_k: int = 3, include_values=True, metadata_filter = None, namespace: str = 'default'):
        index = PineconeService.load_index(index_name)
        if metadata_filter is not None:
            return index.query(
                vector=query_vector,
                top_k=top_k,
                include_values=include_values,
                filter=metadata_filter,
                namespace=namespace
            )

        return index.query(
            vector=query_vector,
            top_k=top_k,
            include_values=include_values,
            namespace=namespace
        )

