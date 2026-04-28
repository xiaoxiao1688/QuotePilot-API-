from fastapi import APIRouter

from app.schemas.common import ModelCatalogEntry, ModelCatalogResponse, ModelInfoResponse
from app.schemas.quote import AnalyzeTextRequest, AnalyzeTextResponse
from app.services.local_risk_model import local_risk_model_service
from app.services.local_text_model import local_text_model_service

router = APIRouter()


@router.get("/model-info", response_model=ModelInfoResponse)
def get_model_info() -> ModelInfoResponse:
    labels = local_risk_model_service.labels
    return ModelInfoResponse(
        model_name=local_risk_model_service.model_name,
        model_path=str(local_risk_model_service.model_path),
        model_loaded=local_risk_model_service.is_loaded,
        labels=labels,
    )


@router.get("/models", response_model=ModelCatalogResponse)
def get_model_catalog() -> ModelCatalogResponse:
    risk_labels = local_risk_model_service.labels
    text_labels = local_text_model_service.labels
    return ModelCatalogResponse(
        models=[
            ModelCatalogEntry(
                model_name=local_risk_model_service.model_name,
                model_path=str(local_risk_model_service.model_path),
                model_loaded=local_risk_model_service.is_loaded,
                labels=risk_labels,
            ),
            ModelCatalogEntry(
                model_name=local_text_model_service.model_name,
                model_path=str(local_text_model_service.model_path),
                model_loaded=local_text_model_service.is_loaded,
                labels=text_labels,
            ),
        ]
    )


@router.post("/analyze-text", response_model=AnalyzeTextResponse)
def analyze_text(payload: AnalyzeTextRequest) -> AnalyzeTextResponse:
    local_text = local_text_model_service.classify_text(payload.text)
    return AnalyzeTextResponse(
        text_preview=payload.text[:200],
        local_text=local_text,
    )
