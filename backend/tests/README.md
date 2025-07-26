# Coinfrs Backend Tests

This directory contains all tests for the Coinfrs backend.

## Test Structure

```
tests/
├── unit/                  # Unit tests for individual components
├── integration/           # Integration tests with external services
│   ├── binance/          # Binance API integration tests
│   └── fireblocks/       # Fireblocks API integration tests (future)
└── e2e/                  # End-to-end tests (future)
```

## Running Tests

### Integration Tests

#### Binance Collectors Test

This test verifies the Binance API client and data collectors work correctly with real API keys.

**Setup:**
1. Add your Binance API credentials to `.env`:
   ```
   # Main Account (required)
   BINANCE_MAIN_API_KEY=your-main-api-key
   BINANCE_MAIN_API_SECRET=your-main-api-secret
   BINANCE_MAIN_EMAIL=main@example.com
   
   # Sub Account (optional)
   BINANCE_SUB_API_KEY=your-sub-api-key
   BINANCE_SUB_API_SECRET=your-sub-api-secret
   BINANCE_SUB_EMAIL=sub@example.com
   ```
   
   Note: The test will automatically test both accounts if sub-account credentials are provided.

2. Ensure your API key has **read-only** permissions for:
   - Enable Reading
   - Enable Spot & Margin Trading (for trade history)
   - Enable Futures (if testing futures transfers)

**Run the test:**
```bash
cd backend
python -m tests.integration.binance.test_collectors
```

**What it tests:**
- API connection and authentication for both main and sub accounts
- Account snapshot retrieval
- All data collectors (deposits, withdrawals, trades, etc.)
- Data fetching without database writes (dry run)
- Sub-account specific features (transfers between accounts)

**Output:**
- Console output showing test results for each account
- JSON files saved to:
  - `tests/integration/binance/results/main/` - Main account results
  - `tests/integration/binance/results/sub/` - Sub account results (if tested)
  - `tests/integration/binance/results/combined_results_*.json` - Combined summary

### Unit Tests

Unit tests will be added as we develop more components.

## Test Guidelines

1. **API Keys**: Never commit real API keys. Always use environment variables.
2. **Read-Only**: Integration tests should only read data, never modify.
3. **Isolation**: Each test should be independent and not affect others.
4. **Documentation**: Document what each test does and its requirements.

## Future Tests

- Unit tests for data processing logic
- Mock API tests for CI/CD pipeline
- End-to-end reconciliation tests
- Performance tests for large datasets