# Binance Reconciliation Tests

This directory contains comprehensive tests for the Binance reconciliation system that verify all collectors and endpoints are working properly.

## Test Files

1. **test_collectors_basic.py** - Quick test to verify all collectors can be instantiated and called
2. **test_full_reconciliation_flow.py** - Comprehensive test that exercises all endpoints with actual API calls
3. **test_raw_data_collection.py** - Original test file (fixed to work with synchronous collectors)

## Running the Tests

### Prerequisites

Set your Binance API credentials as environment variables:
```bash
export BINANCE_API_KEY="your-api-key-here"
export BINANCE_API_SECRET="your-api-secret-here"
```

### Basic Test (Quick Verification)
```bash
python tests/integration/binance/test_collectors_basic.py
```

This test:
- Verifies all collectors can be instantiated
- Makes minimal API calls (1 day of data)
- Shows which collectors are working
- Takes about 30 seconds to run

### Full Reconciliation Test
```bash
python tests/integration/binance/test_full_reconciliation_flow.py
```

This test:
- Tests all collectors with 30 days of historical data
- Generates CSV files for all collected data
- Provides detailed statistics for each collector
- May take several minutes depending on account activity

### Output

CSV files are generated in:
```
/backend/tests/output/exports/binance/{email}/
```

## Collectors Tested

1. **ExchangeInfoCollector** - Trading pairs and symbol information
2. **SnapshotCollector** - Daily balance snapshots
3. **DepositCollector** - Deposit history
4. **WithdrawCollector** - Withdrawal history
5. **TransferCollector** - All transfer types (main/sub accounts, between wallets)
6. **TradeCollector** - Trade history (auto-discovers traded symbols)
7. **ConvertCollector** - Convert transaction history

## Expected Results

Each collector returns a dictionary with:
- Number of items collected
- Number of items saved (if database is available)
- CSV file path (if data was exported)
- Any errors encountered

## Troubleshooting

1. **API Key Issues**
   - Ensure API key has appropriate permissions (read-only is sufficient)
   - Check if API key is enabled for the IP address

2. **No Data Returned**
   - Some collectors may return no data if there's no activity in the date range
   - Try extending the date range in the test files

3. **Trade Collector**
   - Automatically discovers symbols based on user assets
   - May need database connection for full functionality
   - Falls back to testing common symbols if discovery fails

## Raw Data Tables

The collectors populate these raw data tables as defined in `app/models/binance_reconciliation.py`:
- BinanceRawDailySnapshot
- BinanceRawDepositHistory
- BinanceRawWithdrawHistory
- BinanceRawTransferBetweenAccountMainSpot
- BinanceRawTransferBetweenAccountSub
- BinanceRawTransferBetweenWallets
- BinanceRawTrades
- BinanceRawConvertHistory
- BinanceExchangeInfo
- BinanceTradedSymbols