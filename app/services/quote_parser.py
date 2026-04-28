import re

from app.schemas.quote import ParseQuoteRequest, ParseQuoteResponse, ParsedQuoteItem
from app.services.local_risk_model import local_risk_model_service
from app.services.local_text_model import local_text_model_service


class QuoteParserService:
    def parse(self, payload: ParseQuoteRequest) -> ParseQuoteResponse:
        text = payload.source_text.strip()
        lower_text = text.lower()
        warnings: list[str] = []

        quantity = self._extract_first_int(
            text,
            [
                r"(?:x|qty|quantity)\s*[:=]?\s*(\d+)",
                r"(?:\u6570\u91cf)\s*[:：]?\s*(\d+)",
                r"(\d+)\s*(?:pcs|pieces|\u4e2a|\u4ef6|\u5957|\u7bb1)",
            ],
        ) or 1
        unit_price = self._extract_first_float(
            text,
            [
                r"(?:unit[_\s-]?price|price)\s*[:=]?\s*(\d+(?:\.\d+)?)",
                r"(?:\u5355\u4ef7|\u62a5\u4ef7)\s*[:：]?\s*(\d+(?:\.\d+)?)",
                r"(?:rmb|usd|cny)\s*(\d+(?:\.\d+)?)",
            ],
        ) or 0.0
        lead_time_days = self._extract_first_int(
            text,
            [
                r"(?:lead[_\s-]?time|delivery)\s*[:=]?\s*(\d+)",
                r"(?:\u4ea4\u671f|\u8d27\u671f)\s*[:：]?\s*(\d+)",
                r"(\d+)\s*(?:days|day|\u5929)",
            ],
        )
        shipping = self._extract_first_float(
            text,
            [
                r"(?:shipping|freight|delivery fee)\s*[:=]?\s*(\d+(?:\.\d+)?)",
                r"(?:\u8fd0\u8d39|\u7269\u6d41\u8d39)\s*[:：]?\s*(\d+(?:\.\d+)?)",
            ],
        ) or 0.0
        tax_included = any(flag in lower_text for flag in ["tax included", "vat included", "\u542b\u7a0e"])

        product_name = self._extract_product_name(text)

        if unit_price <= 0:
            warnings.append("Unit price was not found in the source text.")
        if lead_time_days is None:
            warnings.append("Lead time was not found in the source text.")

        item = ParsedQuoteItem(
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            currency=payload.currency,
            lead_time_days=lead_time_days,
            line_total=round(quantity * unit_price, 2),
        )

        confidence = 0.55
        if unit_price > 0:
            confidence += 0.2
        if lead_time_days is not None:
            confidence += 0.15
        if product_name != "Unknown product":
            confidence += 0.1

        confidence = min(confidence, 0.98)
        item_total = round(quantity * unit_price, 2)
        shipping_ratio = round(shipping / item_total, 4) if item_total > 0 else 0.0
        local_text = local_text_model_service.classify_text(text)
        local_risk = local_risk_model_service.assess_quote(
            relative_total_cost=1.0,
            average_lead_time_days=lead_time_days,
            parse_confidence=confidence,
            shipping_ratio=shipping_ratio,
            item_count=1,
            has_missing_lead_time=lead_time_days is None,
        )

        return ParseQuoteResponse(
            supplier_name=payload.supplier_name,
            currency=payload.currency,
            items=[item],
            shipping_fee=shipping,
            tax_included=tax_included,
            parse_confidence=confidence,
            warnings=warnings,
            source_preview=text[:200],
            local_risk=local_risk,
            local_text=local_text,
        )

    @staticmethod
    def _extract_first_int(text: str, patterns: list[str]) -> int | None:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _extract_first_float(text: str, patterns: list[str]) -> float | None:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None

    @staticmethod
    def _extract_product_name(text: str) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        parts = re.split(
            r"(?:x\s*\d+|qty\s*\d+|quantity\s*\d+|\u6570\u91cf\s*[:：]?\s*\d+|unit[_\s-]?price|price|\u5355\u4ef7|\u62a5\u4ef7)",
            compact,
            maxsplit=1,
            flags=re.IGNORECASE,
        )
        candidate = parts[0].strip(" :-,") if parts else ""
        return candidate[:80] if candidate else "Unknown product"
