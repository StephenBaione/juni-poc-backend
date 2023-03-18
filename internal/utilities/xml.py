from xml.dom import minidom

from typing import List, Dict, Tuple, Union, Optional, Callable, Any

class XMLAttributes:
    def __init__(self, attribute: str, value: str) -> None:
        self.attribute = attribute
        self.value = value

    def __call__(self) -> tuple:
        return self.attribute, self.value
    
    @staticmethod
    def get_xml_attributes_from_dict(attributes: Dict[str, str]) -> List["XMLAttributes"]:
        return [XMLAttributes(key, val) for key, val in attributes.items()]

class XMLTag:
    def __init__(
            self, 
            tag: str,
            document: minidom.Document,
            attributes: List[XMLAttributes], 
            children: List["XMLTag"] = [], 
            arguments: Dict[str, str] = None
        ) -> None:
        self.tag = tag

        element = document.createElement(tag)

        for attribute in attributes:
            key, val = attribute()
            element.setAttribute(key, val)

        for arg_key, arg_val in arguments.items():
            if arg_key == "text":
                print(arg_val)
                # text = document.createTextNode(arg_val)
                createTextNode = getattr(document, "createTextNode")
                text = createTextNode(arg_val)
                print(text)
                element.appendChild(text)

        for child in children:
            element.appendChild(child.element)

        self.element = element

    @staticmethod
    def cfg_tag_to_xml_tag(document: minidom.Document, cfg: dict, tag: str, cfg_tag: dict, args: dict) -> "XMLTag":
        attributes: Dict[str, str] = cfg_tag['attributes']
        children: List[str] = cfg_tag['children']
        arguments: Dict[str, Dict] = cfg_tag['arguments']

        xml_attributes = XMLAttributes.get_xml_attributes_from_dict(attributes)

        xml_children = []
        if len(children) > 0:
            for child_tag in children:
                child_cfg_tag = cfg[child_tag]
                child_xml_tag = XMLTag.cfg_tag_to_xml_tag(document, cfg, child_tag, child_cfg_tag, args)
                xml_children.append(child_xml_tag)

        xml_arguments = {}
        for key, data in arguments.items():
            tag_args = args.get(tag, {})

            if data['required']:
                required_arg = tag_args.get(key, None)
                if key is None:
                    raise Exception(f"Missing required argument {key}")
                xml_arguments[key] = required_arg

            else:
                arg = tag_args.get(key, None)
                if arg is not None:
                    xml_arguments[key] = arg
                    continue

                default = data.get('default', None)
                if default is not None:
                    xml_arguments[key] = default

        return XMLTag(
            document=document,
            tag=tag,
            attributes=xml_attributes,
            children=xml_children,
            arguments=xml_arguments
        )

class XMLDoc:
    def __init__(self) -> None:
        self.document = minidom.Document()

    def __str__(self) -> str:
        return self.document.toprettyxml(indent="\t")

    def add_tag(self, tag: XMLTag):
        self.document.appendChild(tag)

    def add_tags(self, tags: List[XMLTag]):
        for tag in tags:
            self.document.appendChild(tag)

    def save(self, file_path: str):
        with open(file_path, "w") as f:
            f.write(str(self))