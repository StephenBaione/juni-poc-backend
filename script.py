from data.data_manager import DataManager

from internal.services.pinecone_service import PineconeService, PineConeItem, MetaDataConfig
from internal.services.openai_service import OpenAIClient

import os
import jsonlines

from tqdm import tqdm

from uuid import uuid4

if __name__ == '__main__':
    data_manager = DataManager()
    openai_client = OpenAIClient()
    pinecone_service = PineconeService()

    file_path = os.path.join('.', 'merged_2_prepared.jsonl')
    prompt_completions = data_manager.get_prompt_completion_batches(file_path, 100)

    model = 'curie:ft-personal-2023-02-25-02-27-15'

    embeddings = []
    print('Loading prompts...')
    for prompt_completion in tqdm(prompt_completions):
        embeddings += openai_client.get_embeddings_batch_with_retry(prompt_completion, save=True)

    pinecone_items = []
    for embedding in tqdm(embeddings):
        pinecone_items.append(
            PineConeItem(
            **{
                'id': str(uuid4()), 
                'vector': embedding, 
                'metadata': { 'model': model }
            }))

    PineconeService.upsert_large_batch('curie-med-q-a', pinecone_items, tqdm)
    # create index
    





