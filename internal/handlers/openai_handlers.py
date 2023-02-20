from ..services.openai_service import OpenAIClient

from internal.request_models.openai_requests import ChatMessage

from uuid import uuid4

class OpenAIHandler:
    def __init__(self) -> None:
        self.openai_service = OpenAIClient()

    def handle_completion_request(self, chat_message: ChatMessage, stream=False) -> dict:
        try:
            if stream:
                return self.openai_service.create_completion_stream(
                    model=chat_message.model,
                    prompt=chat_message.message,
                    max_tokens=1000,
                )

            else:
                completion = self.openai_service.create_completion(
                    model=chat_message.model,
                    prompt=chat_message.message,
                    temperature=0.6,
                    max_tokens=3000,
                )

                chat_message = OpenAIClient.decode_completion_to_chat_message(completion, chat_message.model)
                print(chat_message)
                return chat_message

        except Exception as e:
            print(e)
            return None

    @staticmethod
    def completion_stream_generator(stream, chat_message):
        # The first response is going to be the chat message object
        first_chat_message = False

        for chunk in stream:
            print(chunk)
            if not first_chat_message:
                first_chat_message = True
                chat_message = OpenAIClient.decode_completion_to_chat_message(chunk, chat_message.model)

                if chat_message is None:
                    return None

                yield str(chat_message)
            yield chunk['choices'][0]['text']

    def handle_models_request(self) -> dict:
        response = self.openai_service.get_model_list()

        if response.ok:
            return response.json()

        return None

