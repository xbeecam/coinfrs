# Coinfrs Glossary

This glossary defines key terms used throughout the Coinfrs project, including business domain terms, technical concepts, and exchange-specific terminology.

## Business Domain Terms

### Portfolio
The top-level container for organizing digital assets. Can represent:
- A company's entire crypto holdings
- An individual's personal investments
- A fund or group of related entities

### Entity
A legal or organizational unit within a portfolio. Examples:
- Operating Company
- Trading Subsidiary
- Investment Fund
- Personal Account

### Location Group
A user-defined grouping of accounts that should be treated as a single unit for accounting purposes. Each Location Group:
- Maps to one Chart of Accounts type
- Has one Cost Pool (costing method)
- Can span multiple accounts within an exchange

### Minimum Account Level
The most granular level of an account within a data source:
- **Binance**: Spot wallet, margin account, futures account
- **Fireblocks**: Individual vault
- **Ethereum**: Wallet address

### Cost Pool
A collection of assets that share the same costing method for calculating gains/losses:
- **FIFO** (First In, First Out)
- **LIFO** (Last In, First Out)
- **Average Cost**

### Chart of Accounts (COA)
The categorization system for assets in financial reporting:
- Intangible assets at cost
- Inventory at fair value
- Trading assets
- Long-term investments

### Financial Statement Close Process (FSCP)
The monthly workflow to finalize accounting records:
1. Data collection and validation
2. Transaction classification
3. Reconciliation
4. P&L calculation
5. Journal entry generation

## Technical Terms

### Two-Layer Architecture
Our data storage strategy with two distinct layers:
- **Staging Layer**: Raw, immutable data from external sources
- **Canonical Layer**: Processed, normalized data for application use

### ETL (Extract, Transform, Load)
The process of moving data from staging to canonical layer:
- **Extract**: Read from staging tables
- **Transform**: Normalize and validate data
- **Load**: Write to canonical tables

### Reconciliation
Daily process to ensure data completeness:
- Formula: `Position(T-2) + Transactions = Position(T-1)`
- Covers all account types and sub-accounts
- Generates alerts for discrepancies

### Data Source
An external system that provides transaction data:
- Centralized Exchanges (CEX): Binance, Coinbase
- Wallet-as-a-Service (WaaS): Fireblocks
- Self-managed wallets: Ethereum addresses

### Ingestion
The process of fetching data from external APIs and storing in staging layer

### Position Snapshot
A point-in-time record of all asset balances in an account

### Raw Payload
The unmodified JSON response from an external API, stored in JSONB format

### Processing Status
The state of a record in the staging layer:
- `pending`: Not yet processed
- `processed`: Successfully transformed to canonical
- `error`: Failed processing, needs investigation

## Exchange-Specific Terms

### Binance Terms

#### Account Types
- **Spot**: Regular trading account
- **Margin**: Leveraged trading (Cross/Isolated)
- **Futures**: Derivatives trading (USD-M/COIN-M)
- **Earn**: Savings and staking products

#### Income Types
- **Realized PnL**: Profit/loss from closed positions
- **Funding Fee**: Periodic payments in futures trading
- **Commission**: Trading fees
- **Rebate**: Fee discounts or returns
- **Interest**: From margin lending or earn products

#### Sub-accounts
Separate trading accounts under a main account, often used for:
- Risk isolation
- Different trading strategies
- Organizational separation

### Fireblocks Terms

#### Vault
A secure wallet in Fireblocks that holds assets

#### Transaction Status
- `SUBMITTED`: Transaction created
- `PENDING_SIGNATURE`: Awaiting approval
- `BROADCASTING`: Sent to blockchain
- `CONFIRMED`: Finalized on chain

#### MPC (Multi-Party Computation)
Fireblocks' technology for secure key management

## API Terms

### JWT (JSON Web Token)
Stateless authentication token containing:
- User identity
- Permissions
- Expiration time

### Bearer Token
Authorization header format: `Authorization: Bearer <token>`

### Rate Limiting
API request restrictions:
- **Weight**: Points assigned to each endpoint
- **Window**: Time period for limits (per minute/hour)

### Idempotency
Property where repeated API calls produce the same result

### Webhook
HTTP callback for real-time event notifications

## Database Terms

### JSONB
PostgreSQL's binary JSON datatype:
- Supports indexing
- Allows queries inside JSON
- More efficient than regular JSON

### Soft Delete
Marking records as deleted (`deleted_at`) rather than removing them

### UUID (Universally Unique Identifier)
128-bit identifier used as primary keys

### Foreign Key (FK)
Reference to another table's primary key

### Migration
Versioned database schema change

## Celery Terms

### Task
A unit of work executed asynchronously

### Worker
Process that executes tasks from the queue

### Beat
Scheduler for periodic tasks

### Broker
Message queue (Redis) that stores tasks

### Result Backend
Storage for task results

## Accounting Terms

### P&L (Profit and Loss)
Financial statement showing revenues and expenses

### Journal Entry (JE)
Record of a financial transaction in accounting system

### Audit Trail
Complete record of all changes to financial data

### Basis
Original value of an asset for tax purposes

### Realized Gain/Loss
Profit or loss from selling an asset

### Unrealized Gain/Loss
Paper profit or loss from holding an asset

---

This glossary is a living document. Please add new terms as they are introduced to the project.