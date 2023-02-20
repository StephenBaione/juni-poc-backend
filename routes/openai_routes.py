from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse

from internal.request_models import openai_requests

from internal.handlers.openai_handlers import OpenAIHandler

openai_handler = OpenAIHandler()

openai_router = APIRouter(prefix='/openai', tags=['OpenAI'])


@openai_router.post('/completion')
async def completion(chat_message: openai_requests.ChatMessage, response: Response):
    chat_message = openai_handler.handle_completion_request(chat_message)
    if chat_message is None:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'message': 'Internal Server Error'}

    response.status_code = status.HTTP_200_OK
    return chat_message


@openai_router.post('/completion/stream', response_class=StreamingResponse)
async def completion_stream(chat_message: openai_requests.ChatMessage, response: Response):
    try:
        return StreamingResponse(OpenAIHandler.completion_stream_generator(
            openai_handler.handle_completion_request(
                chat_message, stream=True),
            chat_message
        ))

    except Exception as e:
        print(e)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'message': 'Internal Server Error'}

@openai_router.get('/models')
async def models(response: Response):
    models = openai_handler.handle_models_request()
    if models is None:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'message': 'Internal Server Error'}

    response.status_code = status.HTTP_200_OK
    return models
