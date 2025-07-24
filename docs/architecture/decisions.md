# Architecture Decision Records (ADRs)

This document captures the key architectural decisions made in the Coinfrs project and the rationale behind them.

## ADR-001: Data-Source-First Service Architecture

### Status
Accepted (2025-07-23)

### Context
We need to integrate with multiple cryptocurrency exchanges (Binance, Fireblocks, etc.), each with unique:
- Authentication methods (HMAC vs JWT)
- API structures and endpoints
- Data formats and field names
- Rate limiting rules
- Error handling patterns

### Decision
Organize services by data source rather than by function:
```
services/
├── binance/
│   ├── client.py
│   ├── ingestion.py
│   ├── reconciliation.py
│   └── etl.py
└── fireblocks/
    └── (same structure)
```

### Rationale
1. **Encapsulation**: All exchange-specific logic in one place
2. **Maintainability**: Easy to find and fix exchange-specific issues
3. **Scalability**: New exchanges can be added without touching existing code
4. **Team Organization**: One developer can own one exchange integration
5. **Testing**: Exchange-specific tests are grouped together

### Consequences
- ✅ Clear separation of concerns
- ✅ Easier onboarding of new exchanges
- ✅ Reduced risk of cross-exchange bugs
- ⚠️ Some code duplication across exchanges (mitigated by base classes)

---

## ADR-002: Two-Layer Data Architecture

### Status
Accepted (2025-07-16)

### Context
Financial data requires:
- Immutability for audit trails
- Ability to reprocess when bugs are found
- Flexibility to handle different exchange formats
- Consistent internal representation

### Decision
Implement two distinct data layers:
1. **Staging Layer**: Raw, immutable data exactly as received from APIs
2. **Canonical Layer**: Processed, normalized data in standard format

### Rationale
1. **Auditability**: Can always trace back to original data
2. **Reprocessing**: Can fix ETL bugs and rerun without data loss
3. **Debugging**: Easy to see what data exchange actually sent
4. **Compliance**: Meets financial audit requirements

### Consequences
- ✅ Complete audit trail
- ✅ Data integrity guaranteed
- ✅ Can handle exchange API changes gracefully
- ⚠️ Increased storage requirements
- ⚠️ More complex ETL process

---

## ADR-003: UUID Primary Keys

### Status
Accepted (2025-07-23)

### Context
Need to choose between:
- Sequential integer IDs
- UUIDs
- Composite keys

### Decision
Use UUID v4 as primary keys for all tables.

### Rationale
1. **Distribution**: No central sequence generator needed
2. **Security**: IDs cannot be guessed or enumerated
3. **Merging**: Data from different environments can be merged
4. **Scalability**: Ready for distributed systems
5. **API Design**: Consistent ID format across all resources

### Consequences
- ✅ Better security
- ✅ Easier data migration
- ✅ No ID conflicts
- ⚠️ Larger index size
- ⚠️ Less readable in debugging

---

## ADR-004: Celery for Asynchronous Processing

### Status
Accepted (2025-07-16)

### Context
Need asynchronous processing for:
- API data ingestion (can take minutes)
- ETL processing
- Daily reconciliation
- Report generation

### Decision
Use Celery with Redis as broker and result backend.

### Rationale
1. **Maturity**: Battle-tested in production
2. **Features**: Retry logic, scheduling, routing
3. **Monitoring**: Good visibility into task execution
4. **Python Native**: Integrates well with FastAPI
5. **Scalability**: Easy to add more workers

### Consequences
- ✅ Reliable task processing
- ✅ Built-in retry mechanisms
- ✅ Easy horizontal scaling
- ⚠️ Additional infrastructure (Redis)
- ⚠️ Learning curve for developers

---

## ADR-005: FastAPI for REST API

### Status
Accepted (2025-07-16)

### Context
Need to choose web framework for REST API.

### Decision
Use FastAPI instead of Django REST Framework or Flask.

### Rationale
1. **Performance**: Built on Starlette and Pydantic
2. **Type Safety**: Native Python type hints
3. **Documentation**: Automatic OpenAPI/Swagger generation
4. **Modern**: Async support, WebSockets ready
5. **Developer Experience**: Excellent error messages

### Consequences
- ✅ High performance
- ✅ Automatic API documentation
- ✅ Type validation out of the box
- ⚠️ Smaller ecosystem than Django
- ⚠️ Less "batteries included"

---

## ADR-006: PostgreSQL with JSONB for Staging

### Status
Accepted (2025-07-16)

### Context
Need to store raw API responses which are JSON but also need:
- Querying capabilities
- Indexing
- Transactions
- Relationships

### Decision
Use PostgreSQL with JSONB columns for raw data storage.

### Rationale
1. **Flexibility**: Store any JSON structure
2. **Queryability**: Can query inside JSON with SQL
3. **Indexing**: GIN indexes for JSON fields
4. **Single Database**: No need for separate document store
5. **Transactions**: ACID compliance for financial data

### Consequences
- ✅ Best of both SQL and NoSQL
- ✅ Single database to manage
- ✅ Can evolve schema without migrations
- ⚠️ PostgreSQL specific features
- ⚠️ Need to understand JSONB query syntax

---

## ADR-007: JWT for Authentication

### Status
Accepted (2025-07-23)

### Context
Need stateless authentication that works well with:
- Multiple frontend clients
- Mobile apps (future)
- Microservices (future)

### Decision
Use JWT tokens with short-lived access tokens (15 min) and longer refresh tokens (7 days).

### Rationale
1. **Stateless**: No session storage needed
2. **Scalable**: Works with multiple API servers
3. **Standard**: Well-understood by developers
4. **Flexible**: Can embed claims and permissions
5. **Cross-Domain**: Works for SPAs and mobile

### Consequences
- ✅ Scalable authentication
- ✅ No session management
- ✅ Works everywhere
- ⚠️ Token revocation is harder
- ⚠️ Need to handle token refresh

---

## ADR-008: Soft Deletes

### Status
Accepted (2025-07-23)

### Context
Financial systems need to maintain data for compliance and audit.

### Decision
Implement soft deletes using `deleted_at` timestamp instead of hard deletes.

### Rationale
1. **Audit Trail**: Never lose data
2. **Recovery**: Can restore accidentally deleted data
3. **Compliance**: Meet data retention requirements
4. **Analysis**: Can analyze deleted data patterns
5. **Safety**: Reduces risk of data loss

### Consequences
- ✅ Complete audit trail
- ✅ Data recovery possible
- ✅ Compliance friendly
- ⚠️ Need to filter deleted records
- ⚠️ Database size grows over time

---

## Future Decisions to Consider

1. **Caching Strategy**: Redis vs in-memory vs CDN
2. **API Versioning**: URL vs header vs query parameter
3. **Multi-tenancy**: Schema vs row-level vs database
4. **Monitoring**: OpenTelemetry vs custom solution
5. **CI/CD**: GitHub Actions vs GitLab CI vs Jenkins

---

## Decision Process

When making new architectural decisions:
1. Document the context and constraints
2. List alternatives considered
3. Explain the rationale for the decision
4. Identify positive and negative consequences
5. Get team consensus before implementing
6. Review decisions periodically

This is a living document. New ADRs should be added as significant architectural decisions are made.