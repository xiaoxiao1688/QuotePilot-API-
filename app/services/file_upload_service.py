from __future__ import annotations

import asyncio
import io
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.core.config import settings
from app.db.models import ParseTask, TaskStatus
from app.db.session import SessionLocal
from app.repositories.parse_task import parse_task_repository
from app.schemas.quote import ParseQuoteRequest
from app.services.quote_parser import QuoteParserService


class FileUploadService:
    def __init__(self) -> None:
        self.upload_dir = Path(settings.upload_dir)
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024
        self.allowed_extensions = set(settings.allowed_extensions)
        self.allowed_file_types = set(settings.allowed_file_types)
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        if self.upload_dir.is_absolute():
            self.upload_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.upload_dir = Path.cwd() / self.upload_dir
            self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_extension(self, filename: str) -> str:
        return Path(filename).suffix.lower()

    def _generate_unique_filename(self, original_filename: str) -> str:
        ext = self._get_file_extension(original_filename)
        unique_id = uuid.uuid4().hex
        return f"{unique_id}{ext}"

    def validate_file(self, file: UploadFile) -> tuple[bool, str]:
        filename = file.filename or ""
        ext = self._get_file_extension(filename)

        if not ext:
            return False, "File has no extension"

        if ext not in self.allowed_extensions:
            return False, f"File extension '{ext}' is not allowed. Allowed: {', '.join(self.allowed_extensions)}"

        content_type = file.content_type or ""
        if content_type and content_type not in self.allowed_file_types:
            if not self._is_image_or_pdf_extension(ext):
                return False, f"Content type '{content_type}' is not allowed"

        return True, ""

    def _is_image_or_pdf_extension(self, ext: str) -> bool:
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        return ext in image_exts or ext == ".pdf"

    async def save_file(self, file: UploadFile) -> tuple[Path, str]:
        unique_filename = self._generate_unique_filename(file.filename or "unknown")
        file_path = self.upload_dir / unique_filename

        content = await file.read()

        if len(content) > self.max_file_size:
            raise ValueError(f"File size exceeds maximum allowed size of {settings.max_file_size_mb} MB")

        with open(file_path, "wb") as f:
            f.write(content)

        return file_path, unique_filename

    def determine_file_type(self, filename: str, content_type: str | None) -> str:
        ext = self._get_file_extension(filename)
        if ext == ".pdf":
            return "application/pdf"
        if ext in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if ext == ".png":
            return "image/png"
        if ext == ".gif":
            return "image/gif"
        if ext == ".bmp":
            return "image/bmp"
        return content_type or "application/octet-stream"


file_upload_service = FileUploadService()


class ParseTaskService:
    def __init__(self) -> None:
        self.parser_service = QuoteParserService()

    async def process_task(self, task_id: str) -> None:
        from app.db.session import SessionLocal
        from app.repositories.parse_task import parse_task_repository
        from app.db.models import TaskStatus
        from app.repositories.quote_history import quote_history_repository
        from app.schemas.quote import ParseQuoteRequest

        session = SessionLocal()
        try:
            task = parse_task_repository.get_task_by_id(session, task_id)
            if not task:
                return

            parse_task_repository.update_task_status(
                session, task_id, TaskStatus.PROCESSING
            )

            extracted_text = await self._extract_text_from_file(task.file_path, task.file_type)

            if not extracted_text or extracted_text.strip() == "":
                parse_task_repository.update_task_with_error(
                    session, task_id, "Failed to extract text from file. The file may be empty or unreadable."
                )
                return

            parse_request = ParseQuoteRequest(
                supplier_name=f"Uploaded_Quote",
                source_text=extracted_text,
                currency="CNY",
            )

            parsed_result = self.parser_service.parse(parse_request)

            db_record = quote_history_repository.save_parse_result(session, parsed_result)

            parse_task_repository.update_task_with_result(
                session, task_id, parsed_result, result_id=db_record.id
            )

        except Exception as e:
            parse_task_repository.update_task_with_error(
                session, task_id, str(e)
            )
        finally:
            session.close()

    async def _extract_text_from_file(self, file_path: str, file_type: str) -> str:
        if file_type == "application/pdf":
            return await self._extract_text_from_pdf(file_path)
        elif file_type.startswith("image/"):
            return await self._extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    async def _extract_text_from_pdf(self, file_path: str) -> str:
        try:
            import fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            return self._fallback_extract_pdf(file_path)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    async def _extract_text_from_image(self, file_path: str) -> str:
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
            return text
        except ImportError:
            return self._fallback_extract_image(file_path)
        except Exception as e:
            raise ValueError(f"Failed to extract text from image: {str(e)}")

    def _fallback_extract_pdf(self, file_path: str) -> str:
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except ImportError:
            raise ValueError(
                "PDF text extraction requires either 'PyMuPDF' (fitz) or 'pdfplumber'. "
                "Please install one of them: pip install pymupdf or pip install pdfplumber"
            )

    def _fallback_extract_image(self, file_path: str) -> str:
        raise ValueError(
            "Image text extraction requires 'pytesseract' and 'Pillow'. "
            "Please install them: pip install pytesseract pillow. "
            "Note: You also need to install Tesseract OCR engine on your system."
        )


parse_task_service = ParseTaskService()
