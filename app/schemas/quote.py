from pydantic import BaseModel, Field


class ParsedQuoteItem(BaseModel):
    product_name: str
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(default=0, ge=0)
    currency: str = "CNY"
    lead_time_days: int | None = Field(default=None, ge=0)
    line_total: float = Field(default=0, ge=0)


class LocalRiskAssessment(BaseModel):
    risk_level: str
    risk_probability: float = Field(ge=0, le=1)
    model_name: str
    reasons: list[str]


class LocalTextClassification(BaseModel):
    category: str
    document_type: str
    confidence: float = Field(ge=0, le=1)
    model_name: str
    matched_keywords: list[str]


class ParseQuoteRequest(BaseModel):
    supplier_name: str = Field(min_length=1, max_length=100)
    source_text: str = Field(min_length=1)
    currency: str = Field(default="CNY", min_length=3, max_length=8)


class ParseQuoteResponse(BaseModel):
    supplier_name: str
    currency: str
    items: list[ParsedQuoteItem]
    shipping_fee: float = Field(default=0, ge=0)
    tax_included: bool = False
    parse_confidence: float = Field(ge=0, le=1)
    warnings: list[str]
    source_preview: str
    local_risk: LocalRiskAssessment | None = None
    local_text: LocalTextClassification | None = None


class SupplierQuoteInput(BaseModel):
    supplier_name: str = Field(min_length=1, max_length=100)
    items: list[ParsedQuoteItem] = Field(min_length=1)
    shipping_fee: float = Field(default=0, ge=0)
    parse_confidence: float = Field(default=1, ge=0, le=1)


class CompareQuotesRequest(BaseModel):
    demand_title: str = Field(min_length=1, max_length=120)
    quotes: list[SupplierQuoteInput] = Field(min_length=2)


class RankedQuote(BaseModel):
    supplier_name: str
    item_total: float
    shipping_fee: float
    grand_total: float
    average_lead_time_days: float | None
    parse_confidence: float
    score: float
    rank: int
    risk_flags: list[str]
    local_risk: LocalRiskAssessment | None = None


class CompareQuotesResponse(BaseModel):
    demand_title: str
    ranked_quotes: list[RankedQuote]
    recommended_supplier: str
    summary: str


class AnalyzeTextRequest(BaseModel):
    text: str = Field(min_length=1)


class AnalyzeTextResponse(BaseModel):
    text_preview: str
    local_text: LocalTextClassification


class StoredPayloadRecord(BaseModel):
    id: str
    created_at: str
    payload: dict


class QuoteHistoryResponse(BaseModel):
    recent_parses: list[StoredPayloadRecord]
    recent_comparisons: list[StoredPayloadRecord]
