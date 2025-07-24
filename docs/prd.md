# Product Requirements Document: Coinfrs

- **Version:** 1.3
- **Date:** Jul 23, 2025
- **Author:** CW
- **Status:** Final

---

## 1. Introduction & Vision

### 1.1. Product Overview
We are building a B2B SaaS platform that provides automated accounting and reporting for digital assets. Our software will aggregate transaction data from multiple sources, normalize it, apply accounting logic, and generate audit-ready reports and ERP-compatible files.

### 1.2. Vision
To be the gold standard for digital asset accounting, providing unparalleled clarity, accuracy, and compliance for any entity operating in the crypto economy.

### 1.3. Phased Approach
To accelerate time-to-market and gather feedback from our key pilot users as quickly as possible, we will adopt a phased rollout. This document outlines the scope for Phase 1 (our Lean MVP) and Phase 2 (a fast follow-up).

## 2. Market & Strategy

### 2.1. Competitive Advantage
Our key advantage is our team's unique blend of expertise. We are accountants who have been users of competing products. This gives us an unparalleled, "user-first" perspective to build accountant-centric workflows and provide expert, context-aware support that generic tech companies cannot match.

### 2.2. Go-to-Market
Our initial strategy is a closed beta with high-touch onboarding for key pilot users, including **Coinhako**, **Animoca Brands**, and **Forbole**.

## 3. Definitions
(This section remains unchanged and defines the core concepts of Portfolio, Entity, Location Group, Cost Pool, etc.)

| Term | Description |
| :--- | :--- |
| **Data Source** | We identify four distinct types: CEX (Binance), OTC Desk (B2C2), WaaS (Fireblocks), and Self-managed Wallets (Ethereum). |
| **Minimum Account Level** | The most granular level of an account within a data source (e.g., a wallet address for Ethereum, a spot wallet for Binance). |
| **Location Group** | A user-defined aggregation of Minimum Account Levels. Each Data Source must belong to at least one Location Group. |
| **Chart of Accounts (COA)** | Each Location Group must be mapped to a COA type (e.g., Intangible assets at cost, Inventory at fair value). |
| **Cost Pool** | Each Location Group must be mapped to a Cost Pool. A Cost Pool defines the costing methodology (FIFO, LIFO, Average Cost). |
| **Portfolio** | The top-level container, which can be a Group, Company, or Personal portfolio. |
| **Entity** | A component of a portfolio, can be a Company or Personal entity. |

## 4. Target Users and User Journey

### 4.1. Target Users
- **Primary:** Accountants in Crypto Firms.
  - **Goals:** Achieve monthly financial close, deliver accurate information to management, ensure audit compliance, and facilitate data migration to ERP systems.
- **Secondary:** Individual Crypto Owners.
  - **Goals:** Prepare for tax filing and understand the unbiased performance of their portfolio.

### 4.2. User Journey

#### 4.2.1. User Onboarding
1.  **Registration & Login:** Users can register and log in via a Google Account (OAuth) or passwordless email OTP.
2.  **Portfolio & Entity Creation:** A guided, dynamic form helps users create their portfolio and entities. For each Data Source (e.g., Binance), the system will ask for API keys, then fetch and display the sub-accounts for the user to map into Location Groups.
    - **Success Metric:** User completes data entry within 30 minutes and is satisfied with the experience.

#### 4.2.2. Financial Statement Close Process (FSCP)
1.  **Task Generation:** The user sees a dashboard of tasks and their statuses for the close process.
2.  **Configuration:** The user confirms that all wallets, assets, and mappings are up-to-date.
3.  **Data Ingestion & Classification:** Raw data is ingested continuously. The system performs basic, automated classification.
4.  **Completeness Check:** Data is reconciled daily. Alerts are generated for any issues.
5.  **Manual Classification:** The user reviews transactions within each Location Group and manually classifies any unclassified items.
6.  **PnL Calculation:** Once all transactions in a Cost Pool are classified, the user initiates the PnL calculation process. They can review results and re-classify if needed.
7.  **JE Generation:** After confirming the PnL results, the user can generate the Journal Entry export. Balances can be locked to prevent further changes.
    - **Success Metric:** >90% of transactions are classified automatically; the user can finish the entire process in under 1 hour.

## 5. Phased Rollout Plan

### 5.1. Phase 1 (Lean MVP)
The goal of Phase 1 is to deliver the core, end-to-end workflow to our key pilot users and validate our primary value proposition.

| Category | In Scope for Phase 1 |
| :--- | :--- |
| **Data Sources** | **Binance** and **Fireblocks**. |
| **Accounting Method** | **One method** (to be confirmed with Coinhako, likely FIFO). |
| **User Onboarding** | Google Login and Email OTP. |
| **Core Workflow** | The full user journey as defined in section 4.2, from onboarding to classification and PnL calculation. |
| **Export Format** | **Generic CSV Export** of the Journal Entry. |

### 5.2. Phase 2 (Fast Follow)
Based on feedback from Phase 1, we will quickly follow up with these high-priority features.

| Category | In Scope for Phase 2 |
| :--- | :--- |
| **Data Sources** | Add **Ethereum** (Self-Managed Wallets). |
| **Accounting Method** | Add the remaining two accounting methods (LIFO, Average Cost). |
| **Export Format** | Add **Netsuite-specific JE formatting**. |
| **Features** | Begin implementing Rule-Based Transaction Identification. |
| **Onboarding** | Add Authenticator 2FA and Role-Based Access Control (RBAC). |
