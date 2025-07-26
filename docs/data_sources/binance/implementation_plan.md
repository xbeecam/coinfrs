# Binance Reconciliation Implementation Plan

## Overview

This document provides the detailed technical implementation plan for the Binance reconciliation system, incorporating all feedback and design decisions from the planning phase.

## Architecture

### Data Flow
```
Binance API → Raw Data Collection → Internal DB → Processing → Reconciliation DB → Reconciliation Engine → Reporting
                                         ↓
                                   Symbol Discovery
```

### Key Design Principles
1. **Database-First**: Use internal DB for symbol discovery to minimize API calls
2. **Conservative Rate Limiting**: Use only 50% of rate limit (3000/6000 weight per minute)
3. **T+2 Processing**: Optimize for daily batch processing, not real-time
4. **Comprehensive Error Handling**: Graceful degradation with detailed logging
5. **Pandas-Based Processing**: Leverage pandas for efficient bulk operations
6. **Sub-Account Support**: Full support for main and sub-accounts from day one

## Database Schema

### Core Reconciliation Tables

#### 1. BinanceReconciliationTransfer
```sql
CREATE TABLE binance_reconciliation_transfers (
    pid BIGSERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    fid BIGINT NOT NULL,
    external_id VARCHAR(100) NOT NULL,
    datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    txn_type VARCHAR(50) NOT NULL CHECK (txn_type IN ('transfer_in', 'transfer_out', 'txn_fee')),
    txn_subtype VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    wallet VARCHAR(20) NOT NULL CHECK (wallet IN ('SPOT', 'MARGIN', 'FUTURES', 'OPTION')),
    asset VARCHAR(20) NOT NULL,
    amount DECIMAL(36, 18) NOT NULL,
    counter_party VARCHAR(255),
    network VARCHAR(50),
    txn_hash VARCHAR(100),
    match_id BIGINT,
    reconciled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. BinanceReconciliationTrade
```sql
CREATE TABLE binance_reconciliation_trades (
    pid BIGSERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    fid BIGINT NOT NULL,
    external_id VARCHAR(100) NOT NULL,
    datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    txn_type VARCHAR(50) NOT NULL DEFAULT 'trade',
    txn_subtype VARCHAR(50) NOT NULL CHECK (txn_subtype IN ('spot_buy', 'spot_sell', 'maker_fee', 'taker_fee', 'convert_buy', 'convert_sell')),
    email VARCHAR(255) NOT NULL,
    wallet VARCHAR(20) NOT NULL DEFAULT 'SPOT',
    symbol VARCHAR(20) NOT NULL,
    asset VARCHAR(20) NOT NULL,
    amount DECIMAL(36, 18) NOT NULL,
    price DECIMAL(36, 18),
    agg_id BIGINT,
    reconciled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. BinanceReconciliationBalance
```sql
CREATE TABLE binance_reconciliation_balances (
    pid BIGSERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    fid BIGINT NOT NULL,
    external_id VARCHAR(100),
    date DATE NOT NULL,
    email VARCHAR(255) NOT NULL,
    wallet VARCHAR(20) NOT NULL CHECK (wallet IN ('SPOT', 'MARGIN', 'FUTURES', 'OPTION')),
    asset VARCHAR(20) NOT NULL,
    raw_balance DECIMAL(36, 18) NOT NULL DEFAULT 0,
    raw_loan DECIMAL(36, 18) NOT NULL DEFAULT 0,
    raw_interest DECIMAL(36, 18) NOT NULL DEFAULT 0,
    raw_unrealised_pnl DECIMAL(36, 18) NOT NULL DEFAULT 0,
    cal_balance DECIMAL(36, 18),
    cal_loan DECIMAL(36, 18),
    cal_interest DECIMAL(36, 18),
    cal_unrealised_pnl DECIMAL(36, 18),
    variance_in_asset DECIMAL(36, 18),
    variance_in_usd DECIMAL(36, 18),
    usd_price DECIMAL(36, 18),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Supporting Tables

#### 4. BinanceExchangeInfo
```sql
CREATE TABLE binance_exchange_info (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    base_asset VARCHAR(20) NOT NULL,
    quote_asset VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    is_spot_trading_allowed BOOLEAN NOT NULL,
    is_margin_trading_allowed BOOLEAN NOT NULL,
    raw_data JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. BinanceTradedSymbols
```sql
CREATE TABLE binance_traded_symbols (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    last_trade_time TIMESTAMP WITH TIME ZONE NOT NULL,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(email, symbol)
);
```

#### 6. BinanceReconciliationError
```sql
CREATE TABLE binance_reconciliation_errors (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(255),
    error_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(20),
    error_message TEXT NOT NULL,
    raw_error JSONB,
    needs_manual_review BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);
```

#### 7. BinanceRawData Tables
```sql
-- Raw data storage for audit trail
CREATE TABLE binance_raw_daily_snapshot (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    snapshot_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE binance_raw_deposit_history (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    deposit_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE binance_raw_withdraw_history (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    withdraw_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE binance_raw_transfer_between_account_main_spot (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    transfer_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE binance_raw_transfer_between_account_sub (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    transfer_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE binance_raw_transfer_between_wallets (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    transfer_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE binance_raw_trades (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    trade_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE binance_raw_convert_history (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    convert_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Database View
```sql
CREATE VIEW v_binance_user_assets AS
SELECT DISTINCT 
    email,
    asset,
    MAX(last_seen) as last_seen
FROM (
    SELECT email, asset, datetime as last_seen
    FROM binance_reconciliation_transfers
    UNION ALL
    SELECT email, asset, datetime as last_seen
    FROM binance_reconciliation_trades
    UNION ALL
    SELECT email, asset, date as last_seen
    FROM binance_reconciliation_balances
    WHERE raw_balance > 0 OR cal_balance > 0
) AS all_assets
GROUP BY email, asset;
```

## API Client Enhancements

### Error Handling
```python
class BinanceErrorType(Enum):
    API_KEY_INVALID = "API_KEY_INVALID"
    RATE_LIMIT = "RATE_LIMIT"
    PARAMETER_ERROR = "PARAMETER_ERROR"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    NETWORK_ERROR = "NETWORK_ERROR"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    UNKNOWN = "UNKNOWN"
```

### Rate Limiting
Based on Binance's actual rate limits from exchangeInfo:
- **REQUEST_WEIGHT**: 6000 per minute (we'll use 3000 for safety)
- **ORDERS**: 100 per 10 seconds, 200,000 per day
- **RAW_REQUESTS**: 61,000 per 5 minutes

```python
class RateLimiter:
    def __init__(self):
        # Conservative limits (50% of actual)
        self.weight_limit = 3000  # per minute
        self.weight_used = 0
        self.weight_window_start = time.time()
        
    async def acquire(self, weight: int):
        """Wait if necessary to avoid rate limits"""
        current_time = time.time()
        
        # Reset window if minute has passed
        if current_time - self.weight_window_start >= 60:
            self.weight_used = 0
            self.weight_window_start = current_time
        
        # Wait if adding this request would exceed limit
        if self.weight_used + weight > self.weight_limit:
            wait_time = 60 - (current_time - self.weight_window_start)
            logger.info(f"Rate limit approaching, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            self.weight_used = 0
            self.weight_window_start = time.time()
        
        self.weight_used += weight
```

### Endpoint Weights
Common endpoint weights (from Binance documentation):
- `/api/v3/myTrades`: 10
- `/sapi/v1/accountSnapshot`: 2400
- `/sapi/v1/capital/deposit/hisrec`: 1
- `/sapi/v1/capital/withdraw/history`: 1
- `/sapi/v1/sub-account/sub/transfer/history`: 1
- `/sapi/v1/asset/transfer`: 1
- `/sapi/v1/convert/tradeFlow`: 100

### Pagination Strategy
- Use time-based pagination for large datasets
- Process in chunks of 1000 records (Binance max)
- Handle edge cases where last record timestamp equals next batch start

## Data Collection Strategy

### Account Types Support
All functions will support both main and sub-accounts from day one:
- Main account: Uses standard endpoints
- Sub-account: Uses sub-account specific endpoints where applicable

### Symbol Discovery Process
1. Query `v_binance_user_assets` view for all user assets
2. Query `binance_exchange_info` table for SPOT trading pairs
3. Build symbol list where base_asset OR quote_asset matches user assets
4. Prioritize symbols: stablecoins → major coins → others
5. Use cached traded symbols for efficiency

### Daily Collection Workflow
1. **Exchange Info Update** (once for all users)
   - Run at 00:00 UTC
   - Update `binance_exchange_info` table
   
2. **Per-User Collection** (T+2 processing)
   - Process both main and sub-accounts
   - Fetch daily snapshots
   - Collect deposits/withdrawals
   - Process transfers between accounts/wallets
   - Discover and fetch trades
   - Get convert transactions
   
3. **Data Processing**
   - Transform raw data to canonical format
   - Deduplicate using source + external_id
   - Validate data integrity
   
4. **Reconciliation**
   - Calculate expected balances
   - Compare with actual snapshots
   - Investigate variances
   - Generate reports

## Error Handling Strategy

### Symbol Errors
- **Empty result**: Log as info, continue processing
- **Invalid symbol (-1121)**: Refresh exchange info, retry once
- **Other errors**: Log for manual review, continue with next symbol

### API Errors
- **Rate limit**: Wait 60 seconds, retry
- **Invalid API key**: Alert user, halt processing
- **Network errors**: Retry with exponential backoff
- **Unknown errors**: Log and alert for investigation

## Testing Strategy

### CSV Output Format
Each function will generate CSV output for verification against Binance UI:

1. **Daily Snapshot CSV**
   ```csv
   date,email,wallet,asset,raw_balance,raw_loan,raw_interest,raw_unrealised_pnl
   2025-07-26,main@example.com,SPOT,BTC,1.23456789,0,0,0
   2025-07-26,sub@example.com,SPOT,USDT,10000.00,0,0,0
   ```

2. **Transfers CSV**
   ```csv
   datetime,email,txn_type,txn_subtype,wallet,asset,amount,counter_party,network,txn_hash
   2025-07-26 10:00:00,main@example.com,transfer_in,deposit,SPOT,USDT,1000.00,0x123...,BASE,0xabc...
   ```

3. **Trades CSV**
   ```csv
   datetime,email,txn_type,txn_subtype,symbol,asset,amount,price
   2025-07-26 10:00:00,main@example.com,trade,spot_buy,BTCUSDT,BTC,0.1,40000.00
   2025-07-26 10:00:00,main@example.com,trade,spot_sell,BTCUSDT,USDT,-4000.00,40000.00
   2025-07-26 10:00:00,main@example.com,trade,taker_fee,BTCUSDT,BNB,-0.001,400.00
   ```

4. **Reconciliation Summary CSV**
   ```csv
   date,email,wallet,asset,start_balance,transfers_in,transfers_out,trades_in,trades_out,fees,calculated_balance,actual_balance,variance
   2025-07-26,main@example.com,SPOT,BTC,1.0,0,0,0.1,0,-0.001,1.099,1.099,0
   ```

### Test Execution Plan
1. Test each function individually with provided API keys
2. Generate CSV outputs for both main and sub-accounts
3. Compare results with Binance UI
4. Document any discrepancies
5. Iterate until 100% accuracy achieved

## Performance Optimizations

### Database
- Composite indexes on frequently queried columns
- Partitioning by date for large tables (future enhancement)
- Connection pooling for concurrent operations

### Processing
- Pandas for bulk operations
- Batch inserts (1000 records at a time)
- Async/await for I/O operations
- Process symbols sequentially to avoid rate limits

## Monitoring & Alerting

### Discord Notifications
- Daily reconciliation summary
- Variance alerts above threshold
- Error notifications requiring attention
- Processing statistics

### Metrics to Track
- API calls per minute/day
- Processing time per account
- Number of variances found
- Error rates by type

## Security Considerations

### API Keys
- Stored encrypted using existing security.py
- Read-only permissions required
- IP whitelist recommended for production

### Data Protection
- No logging of sensitive amounts in production
- Audit trail for all reconciliation actions
- Role-based access control for viewing data

## Implementation Timeline

- Week 1: Database setup and API client enhancements
- Week 2: Data collectors implementation (with sub-account support)
- Week 3: Processing and reconciliation engine
- Week 4: Testing with real API keys and CSV validation

## Dependencies

### Python Packages
- pandas>=2.0.0
- asyncio
- aiohttp
- sqlalchemy
- alembic

### Infrastructure
- PostgreSQL 13+
- Redis (for rate limiting state)
- Celery (for scheduled tasks)