import logging
import os
from typing import Dict, Any, List
from app.skills.base import BaseSkill
from app.schemas.skill import SkillMeta, SkillExecutionResult
from app.services.document_extractor import document_extractor, DocumentExtractionError, UnsupportedFileTypeError

logger = logging.getLogger("document_intake")


class DocumentIntakeSkill(BaseSkill):
    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_document_intake",
            name="Document & Narrative Intake Skill",
            description="Parses unstructured incident narrative and extracts raw text from attached PDF and image documents via DocumentExtractor.",
            version="2.0.0",
            category="Intake & Extraction"
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        description = input_data.get("incident_description", "")
        documents = input_data.get("documents", [])
        claimed_amount = float(input_data.get("claimed_amount", 0.0))

        processed_documents: List[Dict[str, Any]] = []
        updated_documents: List[Dict[str, Any]] = []
        has_police_report = "police" in description.lower()
        has_photo_evidence = False

        for doc in documents:
            if isinstance(doc, dict):
                doc_name = doc.get("name", "")
                doc_path = doc.get("path", "")
                doc_dict = dict(doc)

                if "police" in doc_name.lower():
                    has_police_report = True
                if "photo" in doc_name.lower() or "image" in doc.get("type", "").lower():
                    has_photo_evidence = True

                # Attempt local raw text extraction if file exists
                if doc_path and os.path.exists(doc_path):
                    try:
                        extracted_doc = document_extractor.extract(doc_path)
                        doc_dict["raw_text"] = extracted_doc.raw_text
                        doc_dict["document_type"] = extracted_doc.document_type
                        doc_dict["pages_count"] = len(extracted_doc.pages)
                        doc_dict["extraction_status"] = "SUCCESS"

                        processed_documents.append({
                            "name": doc_name,
                            "type": extracted_doc.document_type,
                            "pages": len(extracted_doc.pages),
                            "extracted_char_count": len(extracted_doc.raw_text),
                            "status": "SUCCESS",
                        })
                        logger.info(f"Extracted {len(extracted_doc.raw_text)} chars from document '{doc_name}' ({extracted_doc.document_type})")
                    except UnsupportedFileTypeError as e:
                        logger.warning(f"Unsupported document type for '{doc_name}': {e}")
                        doc_dict["extraction_status"] = "UNSUPPORTED_FILE_TYPE"
                        doc_dict["error"] = str(e)
                        processed_documents.append({
                            "name": doc_name,
                            "status": "UNSUPPORTED_FILE_TYPE",
                            "error": str(e)
                        })
                    except DocumentExtractionError as e:
                        logger.warning(f"Document extraction failed for '{doc_name}': {e}")
                        doc_dict["extraction_status"] = "EXTRACTION_FAILED"
                        doc_dict["error"] = str(e)
                        processed_documents.append({
                            "name": doc_name,
                            "status": "EXTRACTION_FAILED",
                            "error": str(e)
                        })
                    except Exception as e:
                        logger.error(f"Unexpected error extracting text from '{doc_name}': {e}")
                        doc_dict["extraction_status"] = "EXTRACTION_FAILED"
                        doc_dict["error"] = str(e)
                        processed_documents.append({
                            "name": doc_name,
                            "status": "EXTRACTION_FAILED",
                            "error": str(e)
                        })
                else:
                    doc_dict["extraction_status"] = "FILE_NOT_FOUND" if doc_path else "NO_PATH_PROVIDED"
                    processed_documents.append({
                        "name": doc_name,
                        "status": doc_dict["extraction_status"],
                        "error": f"File path '{doc_path}' not found on server" if doc_path else "No file path provided"
                    })

                updated_documents.append(doc_dict)
            else:
                updated_documents.append({"name": str(doc)})

        output = {
            "intake_status": "SUCCESS",
            "extracted_document_count": len(documents),
            "processed_documents": processed_documents,
            "updated_documents": updated_documents,
            "has_police_report": has_police_report,
            "has_photo_evidence": has_photo_evidence,
            "claimed_amount": claimed_amount,
            "parsed_narrative_length": len(description),
        }

        reasoning = [
            f"Successfully processed {len(documents)} document attachment(s).",
            f"Police report evidence detected: {has_police_report}.",
            f"Photo evidence detected: {has_photo_evidence}."
        ]

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=0.97,
            output=output,
            reasoning=reasoning
        )

