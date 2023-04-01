import typing
from uuid import uuid4

from fastapi import UploadFile

from data.pinecone.pinecone_index import PineConeIndex
from data.files.pdf import PDFFile, PDFFIleConfig

from ..services.pinecone_service import PineconeService, PineConeItem, ItemCrudResponse





class PineConeHandler:
    def __init__(self) -> None:
        self.pinecone_service = PineconeService()

    def handle_search_by_plain_text(self, text: str, index_name: str, top_k: int = 5) -> typing.List[PineConeItem]:
        # Get embeddings from openai_client
        embeddings = self.openai_client.get_embeddings(text)

        # Search for items from pinecone
        search_result = self.pinecone_service.search(
            index_name=index_name,
            query_vector=embeddings,
            top_k=top_k
        )

        # Return the results
        return search_result

    def get_index(self, index_id):
        return self.pinecone_service.get_index(index_id)
    
    def get_index_by_name(self, index_name: str):
        return self.pinecone_service.get_index_by_name(index_name)
    
    def handle_add_index_to_db(self, pinecone_index: PineConeIndex):
        _id = pinecone_index.id

        if _id is None:
            pinecone_index.set_id()

        result = self.pinecone_service.save_index_to_db(pinecone_index)
        return result
    
    def handle_update_index_in_db(self, pinecone_index: PineConeIndex):
        return self.pinecone_service.update_index_in_db(pinecone_index)

    def delete_index_from_db(self, item_id: str):
        return self.pinecone_service.delete_index_from_db(item_id)
    
    async def handle_consume_pdf(self, file: UploadFile):
        # Extract file_name and verify it is a pdf document
        file_name = file.filename

        if file_name[-3:].lower() != 'pdf':
            return ItemCrudResponse(
                Item={},
                success=False,
                exception=Exception(message='Invalid suffix for what is supposed to be PDF file')
            )
        file_contents = PDFFile.bytes_to_bytes_io(await file.read())

        print(file_contents)
        self.pinecone_service.consume_pdf(
            file_name,
            file_contents
        )

        return ItemCrudResponse(
            Item={},
            success=True,
            exception=None
        )
    
if __name__ == '__main__':
    pc_handler = PineConeHandler()
    text = 'What is a cell?'

    index_name = 'curie-med-q-a'
    top_k = 5

    search_result = pc_handler.handle_search_by_plain_text(text, index_name, top_k)

    print(search_result)
    

