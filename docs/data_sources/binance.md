# Binance Integration Documentation

## Overview

Binance is one of the world's largest cryptocurrency exchanges, offering multiple account types and financial products. This document provides comprehensive coverage of all Binance APIs needed for complete crypto accounting.

## Account Types

### 1. **Spot Account**
- Main trading account for spot markets
- Holds assets for regular trading
- Supports deposits and withdrawals

### 2. **Margin Account**
- **Cross Margin**: Shared margin across all positions
- **Isolated Margin**: Separate margin for each trading pair
- Supports borrowing, lending, and leveraged trading

### 3. **Futures Account**
- **USD-M Futures**: Stablecoin-margined perpetual and delivery futures
- **COIN-M Futures**: Crypto-margined contracts
- Tracks unrealized/realized PnL, funding fees

### 4. **Earn Account**
- **Simple Earn**: Flexible and locked savings products
- **Staking**: On-chain staking products
- Generates interest and staking rewards

### 5. **Sub-Accounts**
- Separate accounts under main account
- Independent balances and trading
- Requires special API permissions

## API Endpoints by Function

### Core Wallet Operations

**Account Snapshot** (Daily Balances)
- `/sapi/v1/accountSnapshot` - Get daily snapshots for all account types
  - Parameters: `type` (SPOT, MARGIN, FUTURES), `startTime`, `endTime`
  - Returns: Daily balance snapshots at 00:00 UTC

**Deposits**
- `/sapi/v1/capital/deposit/hisrec` - Deposit history with network details
  - Includes: Amount, network, tx hash, status, timestamp

**Withdrawals**
- `/sapi/v1/capital/withdraw/history` - Withdrawal history
  - Includes: Amount, network, tx hash, fee, status

**Universal Transfers**
- `/sapi/v1/asset/transfer` - Transfers between accounts
  - Types: SPOT↔MARGIN, SPOT↔FUTURES, etc.

### Spot Trading

**Account Information**
- `/api/v3/account` - Current balances and account status
- `/sapi/v1/asset/tradeFee` - Trading fee rates

**Trade History**
- `/api/v3/myTrades` - All executed trades
  - Returns: Symbol, price, quantity, commission, timestamp

**Convert/Swap**
- `/sapi/v1/convert/tradeFlow` - Convert trade history
  - Quick conversions between assets

**Dust Conversion**
- `/sapi/v1/asset/dust` - Small balance conversions to BNB

### Margin Trading

**Cross Margin**
- `/sapi/v1/margin/borrow-repay` - Borrow/repay history
- `/sapi/v1/margin/interestHistory` - Interest payments
- `/sapi/v1/margin/forceLiquidationRec` - Liquidation records
- `/sapi/v1/margin/capital-flow` - All capital movements

**Isolated Margin**
- `/sapi/v1/margin/isolated/account` - Isolated account info
- `/sapi/v1/margin/isolated/transfer` - Transfer history

### Futures Trading

**Account & Positions**
- `/fapi/v2/account` - Account information
- `/fapi/v2/positionRisk` - Current positions

**Income History** (`/fapi/v1/income`)
Income types include:
- `REALIZED_PNL` - Closed position profit/loss
- `FUNDING_FEE` - Funding fees paid/received
- `COMMISSION` - Trading fees
- `COMMISSION_REBATE` - Fee rebates
- `INSURANCE_CLEAR` - Insurance fund payments
- `TRANSFER` - Account transfers

### Earn Products

**Simple Earn (Flexible)**
- `/sapi/v1/simple-earn/flexible/position` - Current positions
- `/sapi/v1/simple-earn/flexible/history/rewardsRecord` - Interest earned
- `/sapi/v1/simple-earn/flexible/history/subscriptionRecord` - Deposits
- `/sapi/v1/simple-earn/flexible/history/redemptionRecord` - Withdrawals

**Simple Earn (Locked)**
- Similar endpoints for locked products with fixed terms

**Staking**
- `/sapi/v1/onchain-yields/locked/position` - Staking positions
- `/sapi/v1/onchain-yields/locked/history/rewardsRecord` - Staking rewards

### Sub-Account Management

- `/sapi/v1/sub-account/list` - List all sub-accounts
- `/sapi/v1/sub-account/assets` - Sub-account balances
- `/sapi/v1/sub-account/transfer/subUserHistory` - Transfer history

### Other Income

**Rebates**
- `/sapi/v1/rebate/taxQuery` - Trading fee rebates

## Data Collection Strategy

### 1. **Initial Data Load**
For each account type:
1. Fetch historical transactions (limited by API time ranges)
2. Store raw data in staging tables
3. Process through ETL pipeline

### 2. **Daily Reconciliation**
1. Use `/sapi/v1/accountSnapshot` for daily snapshots
2. Fetch all transactions for the day
3. Verify: Balance(T-1) + Transactions = Balance(T)
4. Generate alerts for discrepancies

### 3. **Real-time Updates**
- Poll endpoints based on account activity
- Respect rate limits
- Use appropriate time ranges for each endpoint

## Implementation Considerations

### Rate Limits
- Default: 1200 weight/minute
- Different endpoints have different weights
- Implement exponential backoff

### Time Ranges
- Most endpoints: 90 days
- Futures income: 200 days
- Account snapshot: 30 days

### Pagination
- Most endpoints return max 1000 records
- Use `startTime` and `endTime` for batching
- Some endpoints support `fromId` for pagination

### Data Completeness
To ensure complete accounting coverage:
1. **All Income Sources**: Trading, staking, lending, rebates
2. **All Expenses**: Fees, interest, liquidations
3. **All Transfers**: Between accounts, sub-accounts
4. **All Asset Changes**: Trades, conversions, dust

## Security Requirements

1. **API Keys**: Must be read-only
2. **IP Restrictions**: Recommended for production
3. **Encryption**: All credentials encrypted at rest
4. **Audit Trail**: Store raw API responses

## Error Handling

Common errors:
- `-1021`: Timestamp outside recvWindow
- `-1003`: Too many requests (rate limit)
- `-2010`: Account access restricted
- `-1102`: Mandatory parameter missing

## Testing Checklist

- [ ] Spot deposits/withdrawals
- [ ] Spot trades and fees
- [ ] Margin borrowing/interest
- [ ] Futures PnL and funding
- [ ] Earn interest/rewards
- [ ] Sub-account transfers
- [ ] Daily reconciliation
- [ ] Rate limit handling
- [ ] Error recovery