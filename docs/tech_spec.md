# Technical Specification: Coinfrs

- **Version:** 1.3
- **Date:** Jul 23, 2025
- **Status:** Final

---

## 1. Overview
This document outlines the technical architecture for the Coinfrs platform, aligned with PRD v1.3. It prioritizes a secure, scalable, and modular architecture on the Google Cloud Platform (GCP) to support a phased rollout.

## 2. System Architecture
(This section remains unchanged)

## 3. Technology Stack & GCP Services
(This section remains unchanged)

## 4. Data Architecture: A Two-Layer Model
To ensure data integrity, auditability, and the ability to reprocess data, we will adopt a two-layer database model. This is fundamental to the architecture.

### 4.1. Layer 1: Staging (Raw Data)
-   **Purpose:** To store an immutable, exact copy of the data received from source APIs (e.g., Binance, Fireblocks). This layer is the ultimate source of truth for what the third-party provided.
-   **Schema:** For each data source, we will use a flexible schema with a `JSONB` column to store the raw API response.
-   **Transaction Data Example (`raw_binance_data`):** `id` (PK), `source_raw_id` (text, a unique ID from the source system), `raw_payload` (jsonb), `ingested_at` (timestamp), `processing_status` (enum).
-   **Position Snapshots:** Daily balance snapshots are stored separately:
    - **`raw_binance_position_snapshot`:** `id` (PK), `data_source_id` (FK), `account_type` (enum: spot/margin/futures), `sub_account_id` (nullable), `snapshot_timestamp`, `balances` (jsonb), `ingested_at`
    - **`raw_fireblocks_position_snapshot`:** Similar structure adapted for Fireblocks vault architecture

### 4.2. Layer 2: Canonical (Processed Data)
-   **Purpose:** This is the universal schema that powers the application. All data in this layer is cleaned, standardized, and structured, regardless of its origin.
-   **Schema:** This layer contains the well-defined relational tables that model our business logic. The `transactions` table will have a foreign key (`source_raw_id`) pointing back to the corresponding record in the staging layer for full traceability.

### 4.3. The ETL Process
The transformation from the Staging Layer to the Canonical Layer is handled by our asynchronous Celery workers using efficient bulk-processing methods.

### 4.4. Reconciliation Architecture
-   **Purpose:** Implement daily completeness checks as specified in the PRD to ensure data integrity.
-   **Completeness Check Formula:** Position(T-2) + Transactions = Position(T-1)
-   **Scope:** All account types (spot, margin, futures) including main and sub-accounts
-   **Implementation:** 
    - Daily automated snapshots of all account balances
    - Reconciliation service compares expected vs actual positions
    - Alerts generated for any discrepancies
-   **Service Structure:** Exchange-specific implementations inheriting from common base classes

## 5. Core Implementation Plan & Phased Approach

### 5.1. Authentication
-   **Phase 1:** Google Login (OAuth 2.0) and Email OTP.

### 5.2. User Onboarding & Dynamic Forms
-   **Phase 1:** The full interactive onboarding flow will be implemented for Binance and Fireblocks.

### 5.3. Financial Statement Close Process (FSCP)
-   **PnL Calculation:** This will be built as a complex, asynchronous Celery task to handle large datasets efficiently. 
    -   **Phase 1 Focus:** The initial implementation will focus on delivering the single accounting method required by our pilot users. The underlying architecture will be designed to easily accommodate the other methods in Phase 2.

### 5.4. Service Architecture
-   **Data-Source-First Organization:** Services are organized by exchange rather than by function
-   **Directory Structure:**
    ```
    app/services/
    ├── common/           # Shared base classes and utilities
    ├── binance/          # All Binance-specific services
    │   ├── client.py     # API client
    │   ├── ingestion.py  # Data fetching
    │   ├── reconciliation.py  # Completeness checks
    │   └── etl.py        # Data transformation
    └── fireblocks/       # All Fireblocks-specific services
        └── (same structure)
    ```
-   **Benefits:** 
    - Clear separation of exchange-specific logic
    - Easy to add new exchanges without affecting existing code
    - Simplified debugging and maintenance
    - Natural boundaries for team ownership

## 6. Security
Security is a paramount concern. The following principles and technologies will be applied.

### 6.1. Authentication and Authorization
- **Phase 1:** User authentication will be handled via Google Login (OAuth 2.0) and Email OTP to provide secure and passwordless options.
- **Authorization:** A role-based access control (RBAC) model will be designed for future phases, but initial implementation will rely on user ownership of data.

### 6.2. Secret Management
- **Production:** All application secrets, including database credentials, third-party API keys (for the application itself), and the encryption key for user data, will be managed by Google Secret Manager.
- **Development:** Developers will use environment variables, managed via a `.env` file, which must never be committed to source control.

### 6.3. Credential Encryption
- **API Key Encryption:** User-provided API keys and secrets for third-party services (e.g., Binance, Fireblocks) are sensitive and must be encrypted at rest.
    - **Encryption Standard:** AES-256-GCM will be used for encrypting these credentials before they are stored in the database.
    - **Key Source (POC/Development):** During the proof-of-concept and initial development phase, the AES encryption key will be loaded from the `ENCRYPTION_KEY` environment variable.
    - **Key Management (Production):** For production environments, the reliance on an environment variable for the master encryption key presents a risk. The production architecture **must** be updated to source this key from a dedicated Key Management Service (e.g., Google Cloud KMS or HashiCorp Vault) to ensure secure storage, rotation, and access control. This is a critical prerequisite for a production launch.

### 6.4. Network Security
- All communication between services will be over TLS.
- Firewall rules will be configured to restrict traffic to only necessary ports and services.

### 6.5. API Key Validation
- **Read-Only Enforcement:** Before storing user API credentials, the system validates that they have read-only permissions
- **Exchange-Specific Checks:** Each exchange client implements permission validation appropriate to that platform
- **Rejection of Write Permissions:** API keys with trading, withdrawal, or other write permissions are rejected during onboarding

## 7. API Design

### 7.1. RESTful Principles
- **Resource-Oriented:** URLs identify resources (e.g., `/portfolios`, `/entities`)
- **HTTP Methods:** GET (read), POST (create), PUT (update), DELETE (remove)
- **Stateless:** Each request contains all necessary information
- **Versioning:** API versioned via URL path (`/api/v1/`)

### 7.2. Endpoint Structure
```
/api/v1/
├── /auth/
│   ├── POST   /register              (deprecated)
│   ├── POST   /login                 (deprecated)
│   ├── POST   /refresh
│   ├── POST   /logout
│   ├── GET    /oauth/google
│   ├── POST   /oauth/google/callback
│   ├── POST   /otp/request
│   └── POST   /otp/verify
├── /users/
│   ├── GET    /me
│   └── PUT    /me
├── /portfolios/
│   ├── GET    /         (list)
│   ├── POST   /         (create)
│   ├── GET    /{id}     (retrieve)
│   ├── PUT    /{id}     (update)
│   └── DELETE /{id}     (delete)
├── /entities/
│   └── (similar CRUD structure)
├── /datasources/
│   ├── POST   /
│   ├── GET    /
│   ├── DELETE /{id}
│   └── POST   /{id}/validate
├── /reconciliation/
│   ├── POST   /trigger
│   └── GET    /history
└── /health/
    ├── GET    /
    ├── GET    /db
    └── GET    /redis
```

### 7.3. Authentication Flow
- **JWT Tokens:** Access tokens expire in 15 minutes, refresh tokens in 7 days
- **Token Storage:** Access token in memory, refresh token in httpOnly cookie
- **Google OAuth:** Redirect flow with state parameter for CSRF protection
- **Email OTP:** 6-digit code valid for 5 minutes

### 7.4. Request/Response Standards

**Request Format:**
```json
{
  "data": {
    // Request payload
  }
}
```

**Success Response:**
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "meta": {
    "timestamp": "2025-07-23T10:00:00Z",
    "request_id": "uuid"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error message",
    "details": {
      // Field-specific errors
    }
  },
  "meta": {
    "timestamp": "2025-07-23T10:00:00Z",
    "request_id": "uuid"
  }
}
```

### 7.5. Error Codes
- `VALIDATION_ERROR`: Invalid request data
- `AUTHENTICATION_ERROR`: Invalid or missing credentials
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Resource conflict (e.g., duplicate)
- `RATE_LIMIT_ERROR`: Too many requests
- `INTERNAL_ERROR`: Server error

## 8. Infrastructure

### 8.1. Database Schema Design
- **Normalized Design:** Separate tables for each entity type
- **Audit Fields:** All tables include `created_at`, `updated_at`, `created_by`, `updated_by`
- **Soft Deletes:** `deleted_at` field instead of hard deletes
- **UUID Primary Keys:** For better distribution and security

### 8.2. Caching Strategy
- **Redis Caching:** For frequently accessed data
- **Cache Layers:**
  - Session cache (15 minutes)
  - User data cache (5 minutes)
  - Exchange rate cache (1 hour)
- **Cache Invalidation:** Event-driven invalidation on updates

### 8.3. Queue Management
- **Celery Queues:**
  - `default`: General tasks
  - `ingestion`: Data fetching tasks
  - `etl`: Transformation tasks
  - `reconciliation`: Daily checks
- **Priority Levels:** High, medium, low
- **Retry Policy:** Exponential backoff with max 3 retries

### 8.4. Container Orchestration
- **Docker Compose:** Local development environment
- **Services:**
  - `app`: FastAPI application
  - `worker`: Celery worker
  - `beat`: Celery beat scheduler
  - `postgres`: PostgreSQL database
  - `redis`: Redis cache/broker
- **Volumes:** Persistent data for postgres, code mount for development

### 8.5. Environment Configuration
- **Environment Variables:**
  - `DATABASE_URL`: PostgreSQL connection string
  - `REDIS_URL`: Redis connection string
  - `SECRET_KEY`: JWT signing key
  - `ENCRYPTION_KEY`: AES encryption key
  - `GOOGLE_CLIENT_ID`: OAuth client ID
  - `GOOGLE_CLIENT_SECRET`: OAuth secret
  - `SENTRY_DSN`: Error tracking
- **Configuration Validation:** Pydantic settings with validation on startup