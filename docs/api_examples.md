# API Examples

## Demo Login

```http
POST /api/v1/auth/demo-login
Content-Type: application/json

{
  "nickname": "xiaoxiao"
}
```

## Parse Quote

```http
POST /api/v1/quotes/parse
Content-Type: application/json

{
  "supplier_name": "Shenzhen Parts Co.",
  "currency": "CNY",
  "source_text": "Laptop stand x 10 unit_price 88 lead_time 5 shipping 20 tax included"
}
```

## Compare Quotes

```http
POST /api/v1/quotes/compare
Content-Type: application/json

{
  "demand_title": "Laptop Stand Purchase",
  "quotes": [
    {
      "supplier_name": "Shenzhen Parts Co.",
      "shipping_fee": 20,
      "parse_confidence": 0.92,
      "items": [
        {
          "product_name": "Laptop stand",
          "quantity": 10,
          "unit_price": 88,
          "currency": "CNY",
          "lead_time_days": 5,
          "line_total": 880
        }
      ]
    },
    {
      "supplier_name": "Guangzhou Smart Supply",
      "shipping_fee": 30,
      "parse_confidence": 0.87,
      "items": [
        {
          "product_name": "Laptop stand",
          "quantity": 10,
          "unit_price": 90,
          "currency": "CNY",
          "lead_time_days": 3,
          "line_total": 900
        }
      ]
    }
  ]
}
```

## Analyze Text

```http
POST /api/v1/ai/analyze-text
Content-Type: application/json

{
  "text": "display screen module quotation quantity 20 unit price 320 lead_time 12 shipping 40 tax included"
}
```
