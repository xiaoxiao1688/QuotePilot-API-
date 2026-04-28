from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from app.core.config import settings
from app.schemas.quote import LocalRiskAssessment


class LocalRiskModelService:
    def __init__(self) -> None:
        self.model_name = settings.local_model_name
        self.model_path = Path(settings.local_model_path)
        self._bundle: dict[str, Any] | None = None

    @property
    def is_loaded(self) -> bool:
        return self._bundle is not None

    @property
    def labels(self) -> list[str]:
        bundle = self._load_bundle()
        return list(bundle["labels"])

    def assess_quote(
        self,
        *,
        relative_total_cost: float,
        average_lead_time_days: float | None,
        parse_confidence: float,
        shipping_ratio: float,
        item_count: int,
        has_missing_lead_time: bool,
    ) -> LocalRiskAssessment:
        bundle = self._load_bundle()
        model = bundle["model"]
        labels = list(bundle["labels"])

        lead_time = average_lead_time_days if average_lead_time_days is not None else 30.0
        features = [[
            relative_total_cost,
            lead_time,
            parse_confidence,
            shipping_ratio,
            float(item_count),
            1.0 if has_missing_lead_time else 0.0,
        ]]

        probabilities = model.predict_proba(features)[0]
        best_index = max(range(len(probabilities)), key=lambda idx: probabilities[idx])
        risk_level = labels[best_index]
        risk_probability = round(float(probabilities[best_index]), 4)

        reasons: list[str] = []
        if relative_total_cost < 0.9:
            reasons.append("Total cost is much lower than peers; verify hidden costs.")
        if relative_total_cost > 1.2:
            reasons.append("Total cost is noticeably higher than peers.")
        if average_lead_time_days is None:
            reasons.append("Lead time is missing.")
        elif average_lead_time_days > 14:
            reasons.append("Lead time is long.")
        if parse_confidence < 0.75:
            reasons.append("Parse confidence is low.")
        if shipping_ratio > 0.12:
            reasons.append("Shipping cost ratio is high.")
        if not reasons:
            reasons.append("Current features look relatively stable.")

        return LocalRiskAssessment(
            risk_level=risk_level,
            risk_probability=risk_probability,
            model_name=self.model_name,
            reasons=reasons,
        )

    def _load_bundle(self) -> dict[str, Any]:
        if self._bundle is None:
            self._bundle = joblib.load(self.model_path)
        return self._bundle


local_risk_model_service = LocalRiskModelService()

