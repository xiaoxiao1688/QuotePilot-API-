# Backend Design

## Product Positioning

The mini-program targets buyers who receive supplier quotations through screenshots, PDFs, spreadsheets, and chat messages. The backend turns those mixed inputs into structured quotation records, then compares price, lead time, and risk signals.

## MVP Scope

### User Roles

- Buyer: creates parse and compare tasks, reviews recommendations
- Manager: reviews summary metrics and final supplier choices
- Admin: manages supplier dictionary and system policies

### Core Use Cases

1. User pastes quotation text or uploads a file.
2. Backend extracts supplier information and line items.
3. Backend normalizes units, tax flags, and price fields.
4. User compares several supplier quotations for the same demand.
5. Backend returns a ranked list with a recommendation summary.

## Architecture

### Modules

- `api`: HTTP endpoints
- `schemas`: request and response contracts
- `db.session`: SQLAlchemy engine and session factory
- `db.models`: ORM entities for quote history persistence
- `services.quote_parser`: transforms raw text into structured quotation data
- `services.recommendation`: ranks quotations and produces business-facing advice
- `services.local_risk_model`: loads a packaged scikit-learn model and scores supplier quote risk
- `services.local_text_model`: loads a packaged scikit-learn text model for quote text classification
- `repositories.quote_history`: database-backed parse and comparison history

### Planned Production Components

- Object storage for source files
- OCR worker for image and PDF extraction
- LLM adapter service for robust field extraction
- MySQL for transactional data
- Redis plus queue workers for async parsing jobs

## Domain Model

### Core Entities

- `User`
- `Supplier`
- `QuotationRecord`
- `QuotationItem`
- `ComparisonSession`
- `AuditLog`

### Suggested Tables

- `users`
- `companies`
- `suppliers`
- `quotation_records`
- `quotation_items`
- `comparison_sessions`
- `comparison_results`
- `audit_logs`
- `parse_records`
- `comparison_records`

## Persistence

The current version uses SQLAlchemy ORM with a configurable `DATABASE_URL`.

- Local default: `sqlite:///./data/app.db`
- MySQL target: `mysql+pymysql://...`
- Tables are auto-created at application startup

## API Design

### `POST /api/v1/auth/demo-login`

Returns a demo identity so frontend work can continue before JWT integration.

### `POST /api/v1/quotes/parse`

Input:

- supplier name
- raw extracted text
- optional target currency

Output:

- normalized header fields
- line items
- parse confidence
- warnings

### `POST /api/v1/quotes/compare`

Input:

- demand title
- list of supplier quotations
- optional weighting strategy

Output:

- ranked quotations
- price gap analysis
- recommendation summary
- risk flags

## Recommendation Rules

The MVP uses a transparent scoring model:

- 60% total price
- 25% lead time
- 15% parse confidence

Risk flags are raised for:

- missing lead time
- suspiciously low price
- empty line items

## Local AI Model

The project now includes a small packaged ML model for quote-risk assessment.

- Model type: `scikit-learn` random forest classifier
- Storage: `models/quote_risk_model.joblib`
- Purpose: estimate `low`, `medium`, or `high` operational risk for a supplier quotation
- Runtime: loaded locally from `.venv` without external API calls

Input features:

- relative total cost against the cheapest offer
- average lead time
- parse confidence
- shipping ratio
- item count
- missing lead time flag

The project also includes a small local text classifier.

- Model type: `tf-idf + logistic regression`
- Storage: `models/quote_text_classifier.joblib`
- Purpose: infer quotation category and whether the text is a formal quote, chat quote, or mixed request
- Runtime: loaded locally from `.venv` without external API calls

## AI Integration Plan

### Phase 1

- Rule-based parser for raw text
- Clear schema so frontend can integrate immediately

### Phase 2

- Add a provider adapter for OpenAI-compatible responses
- Force JSON output into a validated schema
- Log source snippets and extraction confidence

### Phase 3

- Use OCR plus LLM for images and PDFs
- Add item matching and unit normalization dictionaries
- Add supplier scoring based on historical delivery quality

## Non-Functional Requirements

- Idempotent parse submission with client request IDs
- Audit logs for compare and approval actions
- Company-level data isolation
- Structured logs for parsing and recommendation failures
