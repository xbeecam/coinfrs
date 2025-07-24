# User Onboarding Implementation Plan

- **Version:** 1.1
- **Date:** Jul 24, 2025
- **Status:** In Progress - Authentication Updates Required

---

## 1. Overview

This document provides a detailed, step-by-step implementation plan for the User Onboarding and core portfolio management features as defined in the **Phase 1 MVP**. It is intended for the developer responsible for building these backend services.

The plan is derived from the following core documents:
- **[Product Requirements Document (PRD)](./prd.md)**: Defines the user journey and features.
- **[Technical Specification](./tech_spec.md)**: Outlines the architecture, API design, and security requirements.
- **[Development Rules](./rules.md)**: Governs the development process and standards.

The primary goal is to build the foundational, exchange-independent services that allow a user to register, create their organizational structure (Portfolios, Entities), and securely add their data sources (e.g., Binance API keys).

## 2. Prerequisites

Before starting this plan, the following foundational tasks **must be completed**. These correspond to **Tasks 5 and 6** in the main `todo.md`.

-   **[x] Task 1: Core Infrastructure Setup**
    -   **[x] 1.1: Alembic Initialization:** The `alembic` directory must be created and configured via `alembic init alembic`.
    -   **[x] 1.2: Database Configuration:** The application must be able to connect to the PostgreSQL database using the `DATABASE_URL` environment variable.
    -   **[x] 1.3: Initial Migration:** An initial Alembic migration must be generated and applied to create all tables from the existing models (`User`, `Portfolio`, `Entity`, `DataSource`, etc.).
    -   **[x] 1.4: Core API Framework:** The main FastAPI application should be set up with:
        -   A versioned API router (`/api/v1`).
        -   Standardized request/response middleware.
        -   A global error handler as specified in the tech spec.
        -   CORS middleware configured.

## 3. Implementation Plan: Onboarding & Portfolio Setup

This plan is broken down into epics, which correspond to the tasks outlined in the main `todo.md`.

---

### **Epic 1: User Authentication (Task 4.1)**
**Status: `In Progress - Requires Passwordless Implementation`**

**Objective:** Implement a secure, JWT-based **passwordless** authentication system for user registration and login, adhering to the tech spec.

#### **Task 1.1: Setup Auth Dependencies & Hashing** - `Completed`
- **Note:** Password hashing implemented but will be deprecated in favor of passwordless auth.

#### **Task 1.2: Implement JWT Service** - `Completed`
- **Details:** JWT service is ready and will be reused for passwordless authentication.

#### **Task 1.3: Implement Google OAuth Authentication** - `Pending`
- **Objective:** Allow users to register and login via Google Account.
- **Endpoint:** `POST /api/v1/auth/oauth/google`
- **Core Logic:**
    1. Redirect user to Google OAuth consent screen.
    2. Handle callback with authorization code.
    3. Exchange code for access token.
    4. Retrieve user info from Google.
    5. Create or update user record with `google_auth_id`.
    6. Generate JWT tokens and return to user.

#### **Task 1.4: Implement Email OTP Authentication** - `Pending`
- **Objective:** Allow passwordless login via 6-digit OTP sent to email.
- **Endpoints:**
    - `POST /api/v1/auth/otp/request` - Send OTP to email
    - `POST /api/v1/auth/otp/verify` - Verify OTP and return tokens
- **Core Logic:**
    1. Generate secure 6-digit OTP.
    2. Store in Redis with 5-minute TTL.
    3. Send OTP via email service.
    4. Verify OTP and generate JWT tokens.
    5. Implement rate limiting to prevent abuse.

#### **Task 1.5: Implement User Info Endpoint & Auth Middleware** - `Completed`
- **Details:** Existing implementation supports all authentication methods.

---

### **Epic 2: Portfolio & Entity Management (Task 7)**
**Status: `Completed`**

**Objective:** Allow authenticated users to create and manage their portfolios and entities.

#### **Task 2.1: Implement Portfolio CRUD API** - `Completed`
#### **Task 2.2: Implement Entity CRUD API** - `Completed`

---

### **Epic 3: Data Source Management (Task 4.2)**
**Status: `Completed`**

**Objective:** Allow users to securely add and manage their exchange API credentials.

#### **Task 3.1: Implement Data Source Creation Endpoint** - `Completed`
#### **Task 3.2: Implement API Key Validation Endpoint** - `Completed`
#### **Task 3.3: Implement Data Source List/Delete Endpoints** - `Completed`

---

## 4. Acceptance Criteria for Completion

The User Onboarding implementation will be considered complete when a developer can:
1.  [ ] Register a new user via Google OAuth.
2.  [ ] Log in with Email OTP and receive JWTs.
3.  [x] Use the access token to create a new Portfolio and an Entity within it.
4.  [x] Add a new Binance Data Source, providing API keys that are stored encrypted.
5.  [x] Successfully validate the stored API keys via the validation endpoint.
6.  [x] List and delete the created resources.
7.  [ ] All API endpoints are documented via OpenAPI/Swagger (needs update for new auth endpoints).
8.  [ ] All code adheres to the project's linting and formatting standards.
9.  [ ] Password-based authentication endpoints are deprecated.
10. [ ] Frontend integration guide is available for both auth methods.

---

## 5. Tech Lead Review Summary

### Overview of Work Completed
This implementation plan is now fully executed. The core backend services for user onboarding, portfolio management, and data source management have been built and are operational. All tasks outlined in Epics 1, 2, and 3 are complete, and the prerequisites, including database migration, have been successfully addressed.

### Key Accomplishments
-   **Authentication:** A JWT-based authentication system is in place. However, it currently uses password-based authentication which needs to be replaced with Google OAuth and Email OTP as per Phase 1 requirements.
-   **Portfolio Management:** Full CRUD APIs for `Portfolio` and `Entity` models have been implemented. All endpoints are protected and scoped to the authenticated user to ensure data privacy.
-   **Data Source Management:** Users can securely add, validate, list, and delete their exchange API credentials. Sensitive keys are encrypted at rest using AES-256-GCM.
-   **Database & Migrations:** The database schema has been defined using `SQLModel` and an initial migration has been successfully generated and applied using `Alembic`. The database is now in sync with the application models.
-   **API Structure:** A versioned API structure (`/api/v1`) has been established, with clear separation of concerns using FastAPI routers for each resource.

### Challenges & Resolutions
-   **Python Version Incompatibility:** The initial models used the `|` union type hint syntax, which is not supported in Python 3.9. This was resolved by replacing it with `Optional` from the `typing` module.
-   **Database Connectivity:** The initial Alembic setup failed due to missing database drivers (`psycopg2`) and incorrect credentials. This was resolved by adding the necessary dependencies and configuring the database URL via a `.env` file.

### Current Status
The backend foundation is mostly complete but requires critical authentication updates. The current password-based authentication must be replaced with passwordless methods (Google OAuth and Email OTP) to meet Phase 1 requirements. Once this is complete, the API will be ready for frontend integration.

### Critical Next Steps
1. **Implement Google OAuth authentication flow**
2. **Implement Email OTP authentication**
3. **Deprecate password-based endpoints**
4. **Update API documentation for new auth methods**
5. **Create frontend integration guide**