from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ModelInfoResponse(BaseModel):
    model_name: str
    model_path: str
    model_loaded: bool
    labels: list[str]


class ModelCatalogEntry(BaseModel):
    model_name: str
    model_path: str
    model_loaded: bool
    labels: list[str]


class ModelCatalogResponse(BaseModel):
    models: list[ModelCatalogEntry]
