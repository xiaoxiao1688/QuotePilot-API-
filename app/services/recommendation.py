from app.schemas.quote import CompareQuotesRequest, CompareQuotesResponse, RankedQuote
from app.services.local_risk_model import local_risk_model_service


class RecommendationService:
    def compare(self, payload: CompareQuotesRequest) -> CompareQuotesResponse:
        grand_totals = [self._grand_total(quote) for quote in payload.quotes]
        min_total = min(grand_totals)
        max_lead = max(
            (
                self._average_lead_time(quote)
                for quote in payload.quotes
                if self._average_lead_time(quote) is not None
            ),
            default=0.0,
        )

        ranked: list[RankedQuote] = []
        for quote in payload.quotes:
            item_total = round(sum(item.line_total for item in quote.items), 2)
            grand_total = round(item_total + quote.shipping_fee, 2)
            avg_lead = self._average_lead_time(quote)
            risk_flags = self._risk_flags(quote, grand_total, min_total)
            shipping_ratio = round(quote.shipping_fee / item_total, 4) if item_total > 0 else 0.0
            local_risk = local_risk_model_service.assess_quote(
                relative_total_cost=(grand_total / min_total) if min_total > 0 else 1.0,
                average_lead_time_days=avg_lead,
                parse_confidence=quote.parse_confidence,
                shipping_ratio=shipping_ratio,
                item_count=len(quote.items),
                has_missing_lead_time=avg_lead is None,
            )

            price_score = 100.0 if grand_total == 0 else min_total / grand_total * 100
            if avg_lead is None or max_lead == 0:
                lead_score = 65.0
            else:
                lead_score = max(30.0, (1 - avg_lead / max_lead) * 100)
            confidence_score = quote.parse_confidence * 100

            score = round(price_score * 0.6 + lead_score * 0.25 + confidence_score * 0.15, 2)

            ranked.append(
                RankedQuote(
                    supplier_name=quote.supplier_name,
                    item_total=item_total,
                    shipping_fee=quote.shipping_fee,
                    grand_total=grand_total,
                    average_lead_time_days=avg_lead,
                    parse_confidence=quote.parse_confidence,
                    score=score,
                    rank=0,
                    risk_flags=risk_flags,
                    local_risk=local_risk,
                )
            )

        ranked.sort(key=lambda item: (-item.score, item.grand_total))
        for index, item in enumerate(ranked, start=1):
            item.rank = index

        winner = ranked[0]
        summary = self._build_summary(payload.demand_title, winner, ranked[1] if len(ranked) > 1 else None)

        return CompareQuotesResponse(
            demand_title=payload.demand_title,
            ranked_quotes=ranked,
            recommended_supplier=winner.supplier_name,
            summary=summary,
        )

    @staticmethod
    def _grand_total(quote) -> float:
        return round(sum(item.line_total for item in quote.items) + quote.shipping_fee, 2)

    @staticmethod
    def _average_lead_time(quote) -> float | None:
        lead_times = [item.lead_time_days for item in quote.items if item.lead_time_days is not None]
        if not lead_times:
            return None
        return round(sum(lead_times) / len(lead_times), 2)

    def _risk_flags(self, quote, grand_total: float, min_total: float) -> list[str]:
        flags: list[str] = []
        if not quote.items:
            flags.append("No line items were provided.")
        if self._average_lead_time(quote) is None:
            flags.append("Lead time is missing.")
        if grand_total < min_total * 0.85:
            flags.append("Price is significantly lower than peers; verify hidden costs.")
        if quote.parse_confidence < 0.7:
            flags.append("Parse confidence is low; review the source manually.")
        return flags

    @staticmethod
    def _build_summary(demand_title: str, winner: RankedQuote, runner_up: RankedQuote | None) -> str:
        if runner_up is None:
            return (
                f"For {demand_title}, {winner.supplier_name} is currently recommended "
                f"with a total cost of {winner.grand_total:.2f}."
            )

        gap = round(abs(runner_up.grand_total - winner.grand_total), 2)
        if winner.grand_total <= runner_up.grand_total:
            gap_text = f"and is cheaper by {gap:.2f}"
        else:
            gap_text = f"while costing {gap:.2f} more"

        return (
            f"For {demand_title}, {winner.supplier_name} ranks first with a score of "
            f"{winner.score:.2f}. Compared with {runner_up.supplier_name}, it wins on overall "
            f"score {gap_text}."
        )
