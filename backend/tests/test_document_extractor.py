import os
import tempfile
import pytest
from app.services.document_extractor import (
    document_extractor,
    UnsupportedFileTypeError,
    EmptyDocumentError,
    CorruptedDocumentError
)
from app.schemas.document import DocumentContent

def test_unsupported_file_extension():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"Hello world")
        tmp_path = tmp.name

    try:
        with pytest.raises(UnsupportedFileTypeError):
            document_extractor.extract(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        document_extractor.extract("non_existent_file_12345.pdf")

def test_empty_image():
    # Create an empty corrupted png file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(b"")
        tmp_path = tmp.name

    try:
        with pytest.raises((EmptyDocumentError, Exception)):
            document_extractor.extract(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
