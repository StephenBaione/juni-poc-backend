import os
import re
import jsonlines
import string

from typing import Callable, Tuple, List

from io import BytesIO

import fitz

import pdfplumber
from pdfplumber.pdf import PDF
from pdfplumber.page import Page

from pypdf import PdfReader

from langchain.document_loaders import UnstructuredPDFLoader, OnlinePDFLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.docstore.document import Document

from pydantic import BaseModel

import fitz

from .files.pdf import PDFFile, PDFFIleConfig

class DataItem:
    def __init__(self, _type, index, text) -> None:
        self._type = _type
        self.index = index
        self.text = text

class ChunkObject(BaseModel):
    FileName: str
    Text: str
    Page: int
    Paragraph: int

class DataManager:
    def __init__(self) -> None:
        self.raw_training_path = os.path.join('.', 'data', 'training_raw')

    @staticmethod
    def generate_pdf_file_from_name_bytes(file_name: str, file_bytes: BytesIO, multicolumn=False):
        pdf_file_config = PDFFIleConfig.pdf_file_config(multicolumn)

        pdf_file = PDFFile(
            file_name=file_name,
            contents=file_bytes,
            pdf_file_config=pdf_file_config
        )

        return DataManager.add_doc_to_pdf_file(pdf_file, multicolumn=multicolumn)

    @staticmethod
    def add_doc_to_pdf_file(pdf_file: PDFFile, multicolumn=False) -> PDF:
        contents = pdf_file.contents

        try:
            if not multicolumn:            
                pdf_file.pdf_doc = PdfReader(contents)

            else:
                pdf_file.pdf_doc = fitz.open(stream=pdf_file.contents)

            return pdf_file
            
        except Exception as e:
            raise e
        
    def chunk_pdf_langchain(self, file_path):
        file_path = os.path.join(self.raw_training_path, '2014_oxford_diagnostic_handbook.pdf')
        loader = PyPDFLoader(file_path=file_path)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
        data = loader.load_and_split(text_splitter)

        from datetime import datetime

        file_name=str(datetime.now())
        folder_path = os.path.join(self.raw_training_path, 'chunks', 'results', 'langchain')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, file_name)

        page_paragraph_count = {}
        chunk_objects = []
        for doc in data:
            metadata = doc.metadata

            source = metadata['source']
            page = metadata['page']

            paragraph_count = page_paragraph_count.get(page, None)
            if paragraph_count is None:
                page_paragraph_count[page] = 1
                paragraph_count = 1
            else:
                page_paragraph_count[page] += 1

            file_name = re.findall('/(\w+).pdf', source)[0]
            text = doc.page_content

            chunk_objects.append(
                ChunkObject(
                    FileName=file_name,
                    Text=text,
                    Page=page,
                    Paragraph=paragraph_count
                )
            )

        # chunks = []
        # for split in split_text:
        #     content = split.page_content.replace('\n', ' ')
        #     content = self.get_printable_chars(content)
        #     chunks.append(content)

        with open(file_path, 'w+') as file:
            for chunk in chunk_objects:
                file.write(chunk['Text'])
                file.write('\n\n---------------- \n\n')

        return chunk_objects
        
    def chunk_pdf(self, pdf_file: PDFFile, save_chunks=True) -> List[ChunkObject]:
        """Chunk the contents of a PDFFile object

        Args:
            pdf_file (PDFFile): PDFFile object to be chunked
            by_paragraph (bool, optional): Control whether to chunk by paragraph or simply chunk size. Defaults to True.
            max_chunk_size (int, optional): Control maximum size of chunk. Defaults to 1500.

        Raises:
            ValueError: _description_

        Returns:
            parse_results (dict): A dictionary containing the results from chunking the pdf in the following format:
                (page_number: int, paragraph_number: int): chunked_text: str
        """
        pdf_doc = pdf_file.pdf_doc
        if pdf_doc is None:
            raise ValueError("PDF Doc must be set before chunking")
        
        multicolumn = pdf_file.pdf_file_config.multicolumn

        docs = []
        if not multicolumn:
            docs = [
                Document(
                    page_content=page.extract_text(),
                    metadata={'source': pdf_file.file_name, "page": i}
                )
                for i, page in enumerate(pdf_doc.pages)
            ]

        else:
            docs = self.get_multicolumn_docs(pdf_file)
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
        data = text_splitter.split_documents(docs)

        page_paragraph_count = {}
        chunk_objects = []
        for doc in data:
            metadata = doc.metadata

            page = metadata['page']

            paragraph_count = page_paragraph_count.get(page, None)
            if paragraph_count is None:
                page_paragraph_count[page] = 1
                paragraph_count = 1
            else:
                page_paragraph_count[page] += 1

            file_name = pdf_file.file_name
            text = doc.page_content

            text = self.get_printable_chars(text)

            chunk_objects.append(
                ChunkObject(
                    FileName=file_name,
                    Text=text,
                    Page=page,
                    Paragraph=paragraph_count
                )
            )

        from datetime import datetime

        file_name = pdf_file.file_name[:-3]
        folder_path = os.path.join(self.raw_training_path, 'chunks', 'results', file_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, f"{str(datetime.now())}_file_name")
        with open(file_path, 'w+') as file:
            for chunk in chunk_objects:
                file.write(chunk.Text)
                file.write('\n\n---------------- \n\n')

        return chunk_objects
    
    def get_multicolumn_docs(self, pdf_file: PDFFile) -> List[Document]:
        doc = pdf_file.pdf_doc

        documents = []
        for page_number, page in enumerate(doc):
            documents.append(
                Document(
                    page_content=page.get_text(),
                    metadata={ 'source': pdf_file.file_name, 'page': page_number }
                )
            )

        return documents
    
    def list_raw_training_files(self):
        return os.listdir(os.path.join('.', 'data', 'training_raw'))

    def separate_topics_content_of_page(self, tcc_page):
        topics_filter = tcc_page.filter(lambda obj: (obj['object_type'] == 'char' and 'Bold' in obj['fontname'] and obj['size'] > 12))
        sub_topics_filter = tcc_page.filter(lambda obj: (obj['object_type'] == 'char' and 'Bold' in obj['fontname'] and '10' in str(obj['size'])))
        content_filter = tcc_page.filter(lambda obj: not (obj['object_type'] == 'char' and 'Bold' in obj['fontname']))
        
        clean_text = tcc_page.extract_text()
        topics_text = topics_filter.extract_text().split('\n')
        sub_topics_text = sub_topics_filter.extract_text().split('\n')
        content_text = content_filter.extract_text().split('\n')

        return {
            "clean_text": clean_text,
            'topics_text': topics_text,
            'sub_topics_text': sub_topics_text,
            'content_text': content_text
        }

    def get_data_items(self, clean_text, values, _type):
        data_indices = {}
        for value in values:
            value = ''.join(v for v in value if v in string.printable)
            index = clean_text.find(value)
            data_indices[index] = (_type, value)
        return data_indices

    def order_topics_subtopics_content(
        self,
        topic_data_items,
        subtopic_data_items,
        content_data_items):

        merged_dict = {}
        merged_dict.update(topic_data_items)
        merged_dict.update(subtopic_data_items)
        merged_dict.update(content_data_items)

        first_topic_indices = list(topic_data_items.keys())
        first_subtopic_indices = list(subtopic_data_items.keys())
        first_content_indices = list(content_data_items.keys())

        sorted_indices = sorted(first_topic_indices + first_subtopic_indices + first_content_indices)

        data_items = []
        for key in sorted_indices:
            _type, value = merged_dict[key]
            data_items.append(
                DataItem(
                    _type,
                    key,
                    value.encode('utf-8', errors='ignore').decode('utf-8')
                )
            )

        import re
        re.sub('', '', '')
        return data_items

    def format_subtopics_to_content_for_jsonl(self, subtopic_to_content: dict):
        data = []

        for subtopic, content in subtopic_to_content.items():
            item = {}

            item['prompt'] = subtopic
            item['completion'] = content

            data.append(item)

        return data

    def split_page_by_paragraph(self, page):
        return page.extract_text().split('\n')

    def extract_paragraphs(self, page: Page, multicolumn = False, num_col_per_page: int = 1):
        if not multicolumn:
            text = page.extract_text(layout=True)
            paragraphs = text.split('\n\n')
            return paragraphs

        else:
            # Determine the factor to multiple dimensions by to read multi-column pdf
            split_factor = float(1 / num_col_per_page)

            left = page.crop((0, 0, split_factor * page.width, page.height))
            right = page.crop((split_factor * page.width, 0, page.width, page.height))

            left_text = left.extract_text(layout=True)
            left_text = self.get_printable_chars(left_text)

            right_text = right.extract_text(layout=True)
            right_text = self.get_printable_chars(right_text)

            left_paragraphs = left_text.split('\n\n')
            right_paragraphs = right_text.split('\n\n')

            return left_paragraphs + right_paragraphs

    def split_large_paragraphs(self, paragraph: str, size_limit: str) -> Tuple[List, int]:
        """Ensure that paragraphs are under maximum size limit. Split paragraphs that are above size limit.

        Args:
            paragraph (str): Chunk of text or "paragraph" that will be split if over size_limit
            size_limit (int): The maximum size that a chunk of text can be

        Returns:
            Tuple[List, int]: Tuple containing list of paragraphs split, and the number of paragraphs in list
        """
        if len(paragraph) > size_limit:
            substrings = []
            lines = paragraph.split('\n')
            current_substring = ''

            for line in lines:
                if line.isspace():
                    continue

                if len(current_substring) \
                + len(line) \
                + 1 <= size_limit:
                    current_substring += '\n' + line
                
                else:
                    if current_substring.isspace() or len(current_substring) < 5:
                        current_substring = ''
                        continue

                    substrings.append(current_substring)
                    current_substring = ''

            if not current_substring.isspace() and len(current_substring) >= 5:
                substrings.append(current_substring)

            if len(substrings) == 0:
                return ([None], 0)

            return (substrings, len(substrings))

        else:
            return ([paragraph], 1)

    def extract_text_and_groups(self, file: pdfplumber.PDF):
        groups = {}
        previous_group = None

        pages_to_parse = file.pages

        print('Extracting text and groups...')
        for page in pages_to_parse:
            page_groups = page.filter(lambda obj: (obj['object_type'] == 'char' and 'Bold' in obj['fontname'] and obj['size'] >= 13))
            page_groups = page_groups.extract_text().split('\n')
            current_group = page_groups[0]

            extracted_text = page.extract_text()
            if extracted_text == '':
                continue

            if current_group == previous_group:
                groups[current_group] += page.extract_text()

            else:
                groups[current_group] = page.extract_text()
                previous_group = current_group

        return groups

    def format_group(self, group: str):
        new_group = ''
        for char in group:
            if char.isalpha() or char.isdigit():
                new_group += char
            elif char == '/' or char == '\\':
                new_group += '_and_'
            else:
                new_group += '_'

        return new_group

    def get_printable_chars(self, text: str) -> str:
        return ''.join(char for char in text if char in string.printable)

    def save_content(self, file_path: str, content: str):
        content = ''.join(x for x in content if x in string.printable)
        with open(file_path, 'w') as file:
            file.write(content)

    def get_prompt_prefix(self, file_name, additional_file_paths: list = None):        
        file_path = os.path.join('data', 'prompt_prefixes')
        if additional_file_paths is not None:
            for add_file_path in additional_file_paths:
                file_path = os.path.join(file_path, add_file_path)

        full_path = os.path.join(file_path, file_name)
        with open(full_path, 'r') as file:
            return file.read()

    def merge_jsonl_files(self, file_path: str, out_file_name: str):
        results = []
        for file in os.listdir(file_path):
            with jsonlines.open(os.path.join(file_path, file), 'r') as reader:
                for line in reader.iter(skip_invalid=True):
                    results.append(line)

        with jsonlines.open(out_file_name, 'a') as writer:
            for line in results:
                writer.write(line)

    def get_prompt_completion_embeddings(self, prompt_completion_file_path: str, get_embedding: Callable):
        with jsonlines.open(prompt_completion_file_path, 'r') as reader:
            counter = 0
            for line in reader.iter(skip_invalid=True):
                if counter >= 4:
                    break

                prompt = line['prompt']
                completion = line['completion']

                embedding = get_embedding(prompt + '\n' + completion)
                counter += 1
                yield embedding

    def get_prompt_completion_batches(self, promp_completion_file_path: str, batch_size: int):
        with jsonlines.open(promp_completion_file_path, 'r') as reader:
            counter = 0
            batch = []
            for line in reader.iter(skip_invalid=True):
                prompt = line['prompt']
                completion = line['completion']

                batch.append(prompt + '\n' + completion)
                counter += 1

                if counter == batch_size:
                    yield batch
                    batch = []
                    counter = 0


# if __name__ == '__main__':
#     file_path = os.path.join('.', 'merged_2_prepared.jsonl')
#     out_file_name = os.path.join('.', 'merged_2_prepared_embedding.txt')

#     data_manager = DataManager()
#     openai_client = OpenAIClient()

#     embeddings = data_manager.get_prompt_completion_embeddings(file_path, openai_client.get_embeddings)
#     with open(out_file_name, 'w') as writer:
#         for embedding in embeddings:
#             writer.write(embedding)

    
