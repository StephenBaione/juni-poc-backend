from pydantic import BaseModel

from typing import Optional, List, Union

from uuid import uuid4

from datetime import datetime

import re

class Template(BaseModel):
    id: Optional[str] = None
    template_name: str
    template_version: int
    tag: str
    template: str
    creator: str
    input_variables: List[str]
    created_at: Optional[str]
    updated_at: Optional[str]

    @staticmethod
    def set_id(template: "Template") -> "Template":
        template.id = str(uuid4())

        return template

    @staticmethod
    def set_date_times(template: "Template") -> "Template":
        template.created_at = str(datetime.now())
        template.updated_at = str(datetime.now())

        return template
    
    @staticmethod
    def set_updated_at(template: "Template") -> "Template":
        template.updated_at = str(datetime.now())

        return template

    @staticmethod
    def get_present_template_variables(template: str) -> List[str]:
        return re.findall(r'{(\w+)}', template)
    
    @staticmethod
    def validate_input_variables(template: "Template") -> bool:
        template_text = template.template
        input_variables = template.input_variables

        present_template_variables = Template.get_present_template_variables(template_text)

        # Ensure each input_variable is present in the template text and visa verso
        if (len(input_variables) != len(present_template_variables)):
            return False
        
        for input_variable in input_variables:
            if input_variable not in present_template_variables:
                return False
            
        return True
    
    @staticmethod
    def validate_input_args(template: "Template", input_args: dict) -> bool:
        input_variables = template.input_variables

        if (len(input_variables) != len(input_args)):
            return False
        
        for input_variable in input_variables:
            if input_args.get(input_variable, None) is None:
                return False
            
        return True
    
    def embed_input_variables(self, input_args: dict) -> Union[str, None]:
        if not Template.validate_input_variables(self, input_args):
            return None
        
        if not Template.validate_input_args(self, input_args):
            return None

        input_variables = self.input_variables
        template = self.template

        for input_variable in input_variables:
            template = re.sub('{' + input_variable + '}', input_args.get(input_variable), template)

        return template

