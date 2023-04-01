from io import BytesIO

import re

from typing import Any, Optional
from pydantic import BaseModel

from pdfplumber.pdf import PDF

class PDFFIleConfig(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    multicolumn: bool
    num_col_per_page: int

    @staticmethod
    def pdf_file_config_from_file_name(file_name: str):
        """Generate PDF Config File from pdf file naming convention

        MULTICOLUMN in file_name?
        - YES -> multicolumn = True
        - NO -> multicolumn = False

        NUM_COL_PER_PAGE in file_name?
        - YES -> num_col_per_page = 1
        - NO -> num_col_per_page = NUM_COL_PER_PAGE_{value}

        Args:
            file_name (str): name of file

        Returns:
            FileConfig: Configuration for PDF file
        """

        file_name_lower = file_name.lower()

        multi_column = False

        num_col_per_page = 1
        num_col_pattern = re.compile(r'num_col_per_page_(\d+)')

        if 'multicolumn' in file_name_lower:
            multi_column = True

        if 'num_col_per_page' in file_name_lower:
            num_col_per_page = re.findall(pattern=num_col_pattern, string=file_name_lower)

        return PDFFIleConfig(
            multicolumn=multi_column,
            num_col_per_page=num_col_per_page
        )

class PDFFile(BaseModel):
    # Enable arbitrary types for pdf doc
    class Config:
        arbitrary_types_allowed = True

    file_name: str
    pdf_file_config: PDFFIleConfig

    # TODO: Contents should be BytesIO, need to check into validation
    contents: Any

    # PDF Document after it has been read into doc by pdfplumber
    # SEE: DataManger.add_doc_to_pdf_file()
    pdf_doc: Optional[PDF]

    @staticmethod
    def bytes_to_bytes_io(file_bytes: bytes):
        try:
            return BytesIO(file_bytes)
        except Exception as e:
            raise e


