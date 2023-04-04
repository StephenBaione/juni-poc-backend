from fastapi import APIRouter

from typing import Optional

from internal.handlers.template_handler import TemplateHandler, Template, ItemCrudResponse

template_router = APIRouter(prefix='/template', tags=['Conversation', 'Template'])
template_handler = TemplateHandler()

@template_router.post('/create')
async def create_template(template: Template) -> ItemCrudResponse:
    return template_handler.handle_create_template(template)

@template_router.get('/creator/{creator}/list')
async def list_templates(creator: str):
    return template_handler.handle_list_templates(creator)

@template_router.get('/{template_name}/{template_version}')
async def get_template(template_name: str, template_version: int) -> ItemCrudResponse:
    return template_handler.handle_get_template(template_name, template_version)

@template_router.post('/{template_name}/{template_version}/update')
async def update_template(template_name: str, template_version: int, template: Template) -> ItemCrudResponse:
    return template_handler.handle_update_template(template_name, template_version, template)

@template_router.delete('/{template_name}/{template_version}')
async def delete_template(template_name: str, template_version: int) -> ItemCrudResponse:
    return template_handler.handle_delete_template(template_name, template_version)
