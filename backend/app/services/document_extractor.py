import os
import time
from typing import List, Optional
from app.schemas.document import DocumentContent, PageContent
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("document_extractor")

# Custom Exceptions
class DocumentExtractionError(Exception):
    """Base exception for document extraction failures."""
    pass

class UnsupportedFileTypeError(DocumentExtractionError):
    """Raised when file extension or MIME type is not supported."""
    pass

class CorruptedDocumentError(DocumentExtractionError):
    """Raised when PDF or image file is corrupted or unparseable."""
    pass

class EmptyDocumentError(DocumentExtractionError):
    """Raised when document contains no extractable text."""
    pass

class OCRExtractionError(DocumentExtractionError):
    """Raised when OCR engine encounters a processing failure."""
    pass


class DocumentExtractor:
    """
    Lightweight, privacy-first local document extraction service supporting
    PDFs (via PyPDF2/pypdf) and images (via EasyOCR).
    
    Operates 100% locally with zero external network or LLM calls.
    """
    _ocr_reader = None  # Singleton EasyOCR reader instance

    def __init__(self):
        self.supported_pdf_exts = {".pdf"}
        self.supported_image_exts = {".png", ".jpg", ".jpeg"}

    @classmethod
    def _get_ocr_reader(cls):
        """
        Lazily initializes the EasyOCR reader singleton instance once per application process.
        """
        if cls._ocr_reader is None:
            try:
                import easyocr
                logger.info(
                    f"Initializing EasyOCR singleton (Languages: {settings.OCR_LANGUAGES}, GPU: {settings.OCR_USE_GPU})"
                )
                cls._ocr_reader = easyocr.Reader(
                    settings.OCR_LANGUAGES,
                    gpu=settings.OCR_USE_GPU,
                    verbose=False
                )
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR engine: {e}")
                cls._ocr_reader = False  # Mark as unavailable
        return cls._ocr_reader

    def extract(self, file_path: str) -> DocumentContent:
        """
        Extracts raw text from a local PDF or image file.
        
        :param file_path: Absolute or relative path to target document file.
        :return: DocumentContent schema object.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: '{file_path}'")

        ext = os.path.splitext(file_path)[1].lower()
        start_time = time.perf_counter()

        if ext in self.supported_pdf_exts:
            result = self._extract_pdf(file_path)
            method = "PyPDF2 / pypdf"
        elif ext in self.supported_image_exts:
            result = self._extract_image(file_path)
            method = "EasyOCR"
        else:
            raise UnsupportedFileTypeError(
                f"Unsupported file extension '{ext}'. Supported types: PDF, PNG, JPG, JPEG."
            )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Structured performance logging (Strict Privacy: No raw document text logged)
        logger.info(
            f"Document extraction completed - "
            f"FileType: '{ext}', Method: '{method}', Pages: {len(result.pages)}, Latency: {elapsed_ms}ms"
        )

        if not result.raw_text or not result.raw_text.strip():
            raise EmptyDocumentError(f"No extractable text found in document '{os.path.basename(file_path)}'")

        return result

    def _extract_pdf(self, file_path: str) -> DocumentContent:
        """
        Extracts text from PDF pages using pypdf / PyPDF2.
        """
        pages_content: List[PageContent] = []
        raw_text_parts: List[str] = []

        try:
            # Try PyPDF2 / pypdf
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                from pypdf import PdfReader

            reader = PdfReader(file_path)
            total_pages = len(reader.pages)

            if total_pages == 0:
                raise EmptyDocumentError(f"PDF document contains 0 pages.")

            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                page_text_clean = page_text.strip()
                
                pages_content.append(PageContent(page=page_num, text=page_text_clean))
                if page_text_clean:
                    raw_text_parts.append(page_text_clean)

        except (UnsupportedFileTypeError, EmptyDocumentError):
            raise
        except Exception as e:
            logger.error(f"PDF extraction error on '{os.path.basename(file_path)}': {e}")
            raise CorruptedDocumentError(f"Failed to parse PDF document. File may be corrupted or encrypted: {e}")

        concatenated_raw_text = "\n\n".join(raw_text_parts)
        return DocumentContent(
            document_type="pdf",
            pages=pages_content,
            raw_text=concatenated_raw_text
        )

    def _extract_image(self, file_path: str) -> DocumentContent:
        """
        Extracts text from an image file using EasyOCR (ignoring bounding boxes).
        """
        try:
            reader = self._get_ocr_reader()

            if reader:
                # Detail=0 returns simple list of recognized text strings
                recognized_lines = reader.readtext(file_path, detail=0)
                extracted_text = " ".join(recognized_lines).strip()
            else:
                # Fallback to PIL basic metadata extraction if OCR reader unavailable
                from PIL import Image
                with Image.open(file_path) as img:
                    extracted_text = f"[Image Document {img.format} {img.size[0]}x{img.size[1]}]"

        except Exception as e:
            logger.error(f"OCR extraction error on image '{os.path.basename(file_path)}': {e}")
            raise OCRExtractionError(f"Failed to perform OCR on image file: {e}")

        page_content = PageContent(page=1, text=extracted_text)
        return DocumentContent(
            document_type="image",
            pages=[page_content],
            raw_text=extracted_text
        )

document_extractor = DocumentExtractor()
