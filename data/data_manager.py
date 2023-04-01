import pdfplumber

import os
import jsonlines
import string

from typing import Callable

class DataItem:
    def __init__(self, _type, index, text) -> None:
        self._type = _type
        self.index = index
        self.text = text

class DataManager:
    def __init__(self) -> None:
        self.raw_training_path = os.path.join('.', 'data', 'training_raw')
    
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

    def extract_paragraphs(self, page, multicolumn = False):
        if not multicolumn:
            text = page.extract_text(layout=True)
            text = ' '.join(text.split(' '))
            paragraphs = text.split('\n\n')
            return paragraphs

        else:
            left = page.crop((0, 0, 0.5 * page.width, page.height))
            right = page.crop((0.5 * page.width, 0, page.width, page.height))

            left_text = left.extract_text(layout=True)
            left_text = ' '.join(left_text.split(' '))
            left_text = self.get_printable_chars(left_text)

            right_text = right.extract_text(layout=True)
            right_text = ' '.join(right_text.split(' '))
            right_text = self.get_printable_chars(right_text)

            left_paragraphs = left_text.split('\n\n')
            right_paragraphs = right_text.split('\n\n')

            return left_paragraphs + right_paragraphs

    def split_large_paragraphs(self, paragraph, prefix_length, suffix_length, size_limit = 2095):
        if len(paragraph) > size_limit:
            prompt_length = prefix_length + len(paragraph) + suffix_length + 1

            if prompt_length >= size_limit:
                substrings = []
                lines = paragraph.split('\n')
                current_substring = ''

                for line in lines:
                    if len(current_substring) \
                    + len(line) \
                    + prefix_length \
                    + suffix_length \
                    + 1 <= size_limit:
                        if line == '\n':
                            continue
                        current_substring += '\n' + line
                    
                    else:
                        substrings.append(current_substring)
                        current_substring = ''
                substrings.append(current_substring)

                return substrings

        else:
            return [paragraph]

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

    
