from ..services.template_service import TemplateService, Template, ItemCrudResponse

class TemplateHandler:
    def __init__(self) -> None:
        self.template_service = TemplateService()

    def handle_create_template(self, template: Template) -> ItemCrudResponse:
        return self.template_service.create_template(template)
    
    def handle_get_template(self, template_name: str, template_version: int):
        return self.template_service.get_template(template_name, template_version)
    
    def handle_update_template(self, template_name: str, template_version: int, template: Template) -> ItemCrudResponse:
        return self.template_service.update_template(template_name, template_version, template)
    
    def handle_list_templates(self, creator: str) -> ItemCrudResponse:
        return self.template_service.list_templates(creator)
    
    def handle_delete_template(self, template_name: str, template_version: int) -> ItemCrudResponse:
        return self.template_service.delete_template(template_name, template_version)
