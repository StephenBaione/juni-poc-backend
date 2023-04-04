from .dynamodb_service import DynamoDBService, ItemCrudResponse, Key

from data.models.conversation.template import Template

class TemplateService:
    def __init__(self) -> None:
        self.dynamodb_service = DynamoDBService('Template')

    def create_template(self, template: Template) -> ItemCrudResponse:
        template = Template.set_id(template)
        template = Template.set_date_times(template)

        return self.dynamodb_service.update_item(template)
    
    def get_template(self, template_name: str, template_version: int) -> ItemCrudResponse:
        # query_key = Key('template_name').eq(template_name) & Key('template_version').eq(template_version)
        query_key = {
            'template_name': template_name,
            'template_version': template_version
        }

        return self.dynamodb_service.get_item(None, id_keys=query_key)
    
    def update_template(self, template_name: str, template_version: int, template: Template) -> ItemCrudResponse:
        # Check if template exists
        result = self.get_template(template_name, template_version)

        if not result.success or result.Item == {}:
            return result

        template = Template.set_updated_at(template)
        return self.dynamodb_service.update_item(template)
    
    def list_templates(self, creator: str):
        query_key = Key('creator').eq(creator)

        return self.dynamodb_service.scan_table(query_key)
    
    def delete_template(self, template_name: str, template_version: int) -> ItemCrudResponse:
        query_key = {
            'template_name': template_name,
            'template_version': template_version
        }

        return self.dynamodb_service.delete_item(None, item_key=query_key)
