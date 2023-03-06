from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse

from internal.request_models import openai_requests

from internal.handlers.openai_handlers import OpenAIHandler

openai_handler = OpenAIHandler()

openai_router = APIRouter(prefix='/openai', tags=['OpenAI'])

