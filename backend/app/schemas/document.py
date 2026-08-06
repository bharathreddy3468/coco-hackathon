from typing import List
from pydantic import BaseModel, Field

class PageContent(BaseModel):
    page: int = Field(..., description="1-based page number")
    text: str = Field(..., description="Extracted raw text from page")

class DocumentContent(BaseModel):
    document_type: str = Field(..., example="pdf", description="Document type: 'pdf' or 'image'")
    pages: List[PageContent] = Field(default_factory=list, description="Page-wise extracted text list")
    raw_text: str = Field(..., description="Concatenated raw document text")
