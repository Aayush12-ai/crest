// folder structure only!! baki baad me dekhte h (day2)

aim :>> 
crest/
│
├── apps/                          # Entry points (separate deployable services)
│
│   ├── api-gateway/               # Public entry (ALL traffic comes here)
│   │   ├── routes/
│   │   │   ├── ingest.py          # ONE definitive endpoint
│   │   │   └── health.py
│   │   ├── middleware/
│   │   │   ├── auth.py
│   │   │   ├── rate_limit.py
│   │   │   ├── validation.py
│   │   │   └── logging.py
│   │   └── main.py
│   │
│   ├── ingestion-service/         # Channel adapters (webhooks live here)
│   │   ├── channels/
│   │   │   ├── whatsapp.py
│   │   │   ├── email.py
│   │   │   ├── twitter.py
│   │   │   └── phone.py
│   │   ├── transformers/
│   │   │   └── to_unified_schema.py
│   │   ├── security/
│   │   │   ├── signature_verify.py
│   │   │   └── abuse_detection.py
│   │   └── main.py
│   │
│   ├── processing-service/        # Normalization + routing
│   │   ├── normalization/
│   │   │   ├── schema_mapper.py
│   │   │   ├── language_detector.py
│   │   │   ├── text_cleaner.py
│   │   │   ├── pii_masking.py
│   │   │   └── deduplicator.py
│   │   ├── router/
│   │   │   └── event_router.py
│   │   └── main.py
│   │
│   ├── ai-service/                #  AI engine (isolated for scaling)
│   │   ├── agents/
│   │   ├── rag/
│   │   ├── embeddings/
│   │   ├── ner/
│   │   ├── guardrails/
│   │   │   ├── input_filter.py
│   │   │   ├── output_validator.py
│   │   │   └── safety_rules.py
│   │   ├── classifiers/
│   │   └── main.py
│   │
│   ├── persistence-service/       #  Data layer abstraction
│   │   ├── db/
│   │   │   ├── postgres.py
│   │   │   ├── redis.py
│   │   │   ├── elasticsearch.py
│   │   │   ├── neo4j.py
│   │   │   └── vector_store.py
│   │   ├── repositories/
│   │   └── main.py
│   │
│   ├── sla-service/               #  SLA + workflows
│   │   ├── workflows/
│   │   │   ├── complaint_flow.py
│   │   ├── escalation/
│   │   │   ├── rules.py
│   │   │   └── notifier.py
│   │   ├── schedulers/
│   │   └── main.py
│   │
│   ├── notification-service/      # Emails / Slack / WhatsApp replies
│   │   ├── providers/
│   │   │   ├── email.py
│   │   │   ├── slack.py
│   │   │   └── whatsapp.py
│   │   └── main.py
│   │
│   └── frontend/                  #  Next.js dashboard
│       └── (your existing app)
│
│
├── shared/                        #  Shared logic across services
│   ├── schemas/                   # Unified JSON schema (VERY IMPORTANT)
│   ├── utils/
│   ├── config/
│   ├── constants/
│   └── logger/
│
│
├── messaging/                     # Event backbone
│   ├── kafka/
│   │   ├── producer.py
│   │   ├── consumer.py
│   │   └── topics.py
│   └── redis_queue/
│
│
├── observability/                 # Monitoring & debugging
│   ├── logging/
│   ├── metrics/
│   ├── tracing/
│
│
├── audit/                         # Compliance & tracking
│   ├── audit_trail.py
│   ├── event_logger.py
│   └── policies.py
│
│
├── tests/                         # Testing layer
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── ai_eval/
│
│
├── infra/                         # DevOps
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   └── Dockerfiles/
│   ├── k8s/
│   ├── terraform/
│   └── ci-cd/
│
│
├── scripts/                       # Dev utilities
│   ├── seed_data.py
│   ├── replay_events.py           # replay system (very useful)
│   └── migrations/
│
│
├── .env
├── README.md
└── docs/                          # Architecture docs
