from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from app.core.config import settings
from app.schemas.quote import LocalTextClassification


class LocalTextModelService:
    def __init__(self) -> None:
        self.model_name = settings.local_text_model_name
        self.model_path = Path(settings.local_text_model_path)
        self._bundle: dict[str, Any] | None = None

    @property
    def is_loaded(self) -> bool:
        return self._bundle is not None

    @property
    def labels(self) -> list[str]:
        bundle = self._load_bundle()
        categories = bundle["category_labels"]
        document_types = bundle["document_type_labels"]
        return [f"category:{label}" for label in categories] + [f"document_type:{label}" for label in document_types]

    def classify_text(self, text: str) -> LocalTextClassification:
        bundle = self._load_bundle()
        category_pipeline = bundle["category_pipeline"]
        document_pipeline = bundle["document_pipeline"]

        category_probabilities = category_pipeline.predict_proba([text])[0]
        category_labels = list(category_pipeline.classes_)
        category_index = max(range(len(category_probabilities)), key=lambda idx: category_probabilities[idx])

        document_probabilities = document_pipeline.predict_proba([text])[0]
        document_labels = list(document_pipeline.classes_)
        document_index = max(range(len(document_probabilities)), key=lambda idx: document_probabilities[idx])

        category = str(category_labels[category_index])
        document_type = str(document_labels[document_index])
        confidence = round((float(category_probabilities[category_index]) + float(document_probabilities[document_index])) / 2, 4)

        matched_keywords = self._matched_keywords(text)

        return LocalTextClassification(
            category=category,
            document_type=document_type,
            confidence=confidence,
            model_name=self.model_name,
            matched_keywords=matched_keywords,
        )

    @staticmethod
    def _matched_keywords(text: str) -> list[str]:
        lower_text = text.lower()
        keywords = [
            "quote",
            "报价",
            "tax included",
            "含税",
            "lead_time",
            "交期",
            "shipping",
            "运费",
            "box",
            "包装",
            "laptop",
            "screen",
            "sensor",
            "cable",
        ]
        return [keyword for keyword in keywords if keyword in lower_text][:6]

    def _load_bundle(self) -> dict[str, Any]:
        if self._bundle is None:
            self._bundle = joblib.load(self.model_path)
        return self._bundle


local_text_model_service = LocalTextModelService()

