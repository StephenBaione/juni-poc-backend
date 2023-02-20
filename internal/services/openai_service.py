from dotenv import load_dotenv

import os
import json
import openai

import requests

from tqdm import tqdm

import backoff

from uuid import uuid4

from ..request_models.openai_requests import ChatMessage

from dotenv import load_dotenv

class OpenAIClient:
    def __init__(self) -> None:
        load_dotenv()

        self.api_key: str = os.getenv('OPENAI_API_KEY')
        if self.api_key is None:
            raise EnvironmentError("API_KEY must be provided in .env file.")

        self.organization_id: str = os.getenv('OPENAI_ORGANIZATION_ID')
        if self.organization_id is None:
            raise EnvironmentError('ORGANIZATION_ID must be provided in .env file.')

        openai.api_key = self.api_key
        openai.organization = self.organization_id

        self.cfg = self.__load_api_cfg()
        if self.cfg is None:
            raise FileNotFoundError('Unable to load cfg.')

    def __load_api_cfg(self):
        cfg = None
        with open(os.path.join(os.path.dirname(__file__), 'cfg', 'api_config.json')) as file:
            cfg = json.load(file)

        return cfg

    def __get_authorization_header(self, json_content_type = True):
        """
        Return Bearer Authorization header.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Organization": self.organization_id
        }

        if json_content_type:
            headers['Content-Type'] = 'application/json'

        return headers

    def make_request(self, endpoint_name: str, body = None, url_suffix = None, path_params = None):
        """Make GET and POST requests to OpenAI API

        Args:
            endpoint_name (str): Name of endpoint to be requested

        Returns:
            requests.Response: Response object containing results of HTTP request
        """
        cfg = self.cfg

        endpoint_cfg = cfg['endpoints'][endpoint_name]
        
        url: str = endpoint_cfg['url']
        if endpoint_cfg.get('path_params', None) is not None:
            cfg_path_params = endpoint_cfg['path_params']
            if cfg_path_params is None:
                raise ValueError(f"{endpoint_name} requires path params {', '.join(cfg_path_params)}.")

            for cfg_path_param in cfg_path_params:
                path_param = path_params.get(cfg_path_param, None)
                if path_param is None:
                    raise ValueError(f"{cfg_path_param} must be provided as a path parameter.")

                url = url.replace('{' + cfg_path_param + '}', path_param)

        headers: dict = endpoint_cfg['headers']
        authorization_bearer = headers.get('Authorization_Bearer', False)
        if authorization_bearer:
            headers['Authorization'] = f"Bearer {self.api_key}"
            del headers['Authorization_Bearer']

        include_organization: bool = headers.get('Include_Organization', False)
        if include_organization:
            headers['OpenAI-Organization'] = self.organization_id
            del headers['Include_Organization']

        method: str = endpoint_cfg['method']
        params: dict = endpoint_cfg.get('params', None)

        resp: requests.Response or None = None
        if method == 'GET':
            if params is not None:
                resp = requests.get(url, params=params, headers=headers)
            
            resp = requests.get(url, headers=headers)

        elif method == 'POST':
            cfg_body = endpoint_cfg['body']

            required_options = cfg_body['required']
            if len(required_options) > 0 and body is None:
                raise ValueError(f"Must provide body that matches {endpoint_name} required fields.")

            for required_option in required_options:
                if body.get(required_option, None) is None:
                    raise ValueError(f"{required_option} Must be provided in requrest body.")

            resp = requests.post(
                url,
                headers=headers,
                json=body
            )

        elif method == 'DELETE':
            resp = requests.delete(
                url,
                headers=headers
            )

        return resp

    def get_model_list(self):
        return self.make_request('model_list')

    def save_to_results_file(self, data_to_append: dict):
        results = None
        with open(os.path.join('.', 'results.json'), 'r') as file:
            results = json.load(file)
            results['results'].append(data_to_append)

        with open(os.path.join('.', 'results.json'), 'w') as file:
            json.dump(results, file)

    def create_completion(
        self,
        model, 
        prompt, 
        temperature=0.7,
        max_tokens=800,
        stop=None,
        **kwargs
    ):

        if stop is not None:
            return openai.Completion.create(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs
            )

        else:
            return openai.Completion.create(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs
            )

    @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
    def create_completion_with_retry(
        self, 
        model, 
        prompt, 
        temperature=0.7,
        max_tokens=800,
        stop=None,
        **kwargs):
        return self.create_completion(model, prompt, temperature, max_tokens, stop, **kwargs)

    def create_completion_stream(
        self,
        model,
        prompt,
        temperature=0.7,
        max_tokens=3000,
        stop=None,
        **kwargs
    ):
        try:
            # If completion stream is requested, return iterable
            yield openai.Completion.create(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                stream=True,
                **kwargs
            )

        except Exception as e:
            print(e)
            return None

    @staticmethod
    def create_openai_chat_message(model, message):
        chat_message_data = {}
        chat_message_data['id'] = 'openai-' + str(uuid4())
        chat_message_data['user'] = 'stephenbaione'
        chat_message_data['sender'] = model
        chat_message_data['message'] = message
        chat_message_data['model'] = model
        chat_message_data['created'] = ''
        chat_message_data['updated'] = ''

        return ChatMessage(**chat_message_data)

    @staticmethod
    def decode_completion_to_chat_message(completion, model):
        choices = completion['choices']
        if len(choices) == 0:
            return None

        message = choices[0]['text']
        message = message.strip()
        return OpenAIClient.create_openai_chat_message(model, message)
        
        
    def create_fine_tune(self, training_file, model="ada", **options):
        """Create a fine tune model.

        Args:
            training_file (str): OpenAI File ID
            model (str, optional): Specify which base model to use. Defaults to "ada".
            options:
                "validation_file",
                "n_epochs",
                "batch_size",
                "learning_rate_multiplier",
                "prompt_loss_weight",
                "compute_classification_metrics",
                "classification_n_classes",
                "classification_positive_class",
                "classification_betas",
                "suffix"

        Returns:
            _type_: _description_
        """
        body = {
            'training_file': training_file,
            'model': model
        }

        body.update(options)
        return self.make_request('create_fine_tune', body)

    def list_fine_tunes(self):
        return self.make_request('list_fine_tunes')

    def retrieve_fine_tune(self, fine_tune_id):
        return self.make_request('retrieve_fine_tune', url_suffix=fine_tune_id)

    def delete_fine_tune(self, model):
        path_params = { 'model': model }
        return self.make_request('delete_fine_tune', path_params=path_params)

    def upload_file(self, file, purpose):
        result = openai.File.create(file, purpose)
        return result

    def retrieve_file(self, file_id):
        path_params = { 'file_id': file_id }
        return self.make_request('retrieve_file', path_params=path_params)

    def retrieve_file_content(self, file_id):
        path_params = {'file_id': file_id}
        return self.make_request('retrieve_file_content', path_params=path_params)

    def list_files(self):
        return self.make_request('list_files')

    def delete_file(self, file_id):
        path_params = {'file_id': file_id}
        return self.make_request('delete_file', path_params=path_params)

    def fix_json_string(self, string):
        import re
        # remove all newline characters
        string = re.sub(r'\n', '', string)
        # add comma after each object except for the last one
        string = re.sub(r'}(\s)(?!})', '},', string)
        # wrap the string in square brackets to make it a valid json array string
        return string

    
# ft-flAx5eIeboyMYTc50W2KnEfK


