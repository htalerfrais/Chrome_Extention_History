# Backend Modular Architecture

## Module boundaries

- `assistant`: chatbot orchestration and tool execution runtime (LangGraph).
- `session_intelligence`: clustering workflows and session semantic analysis.
- `recall_engine`: topic tracking and spaced-recall scheduling.
- `learning_content`: quiz and flashcard generation/evaluation.
- `identity`: token validation and user resolution.
- `outbox`: reliable event publication and worker processing.
- `shared`: ports/contracts shared between modules.

## Layering conventions

Each module follows:

- `domain/`: pure business rules, no framework/IO dependencies.
- `application/`: use-cases orchestrating business flows.
- `infrastructure/`: adapters to DB/LLM/queues and external systems.
- `api/`: router + HTTP contract mapping.

## Dependency rules

1. `application` can depend on `domain` and `shared` ports.
2. `infrastructure` implements ports used by `application`.
3. Modules communicate through explicit ports/events, not direct cross-layer calls.
4. `main.py` remains a thin API shell; object wiring happens in `core/container.py`.
5. Production paths MUST NOT depend on `app/services/*` (legacy removed).

## Event-driven reliability

- Outbox records business events transactionally.
- Worker claims `pending` events, processes handlers, marks as `sent` or `failed`.
- Events are versioned (`event_type`, `event_version`) with idempotency keys.
- Handlers must be idempotent.
