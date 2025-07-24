# Binance API constants and configuration

# API Endpoints
BASE_URL = "https://api.binance.com"
BASE_URL_TESTNET = "https://testnet.binance.vision"

# Endpoints organized by category
ENDPOINTS = {
    # === WALLET API ===
    # Deposits
    "deposit_history": "/sapi/v1/capital/deposit/hisrec",
    "deposit_address": "/sapi/v1/capital/deposit/address",
    "deposit_address_list": "/sapi/v1/capital/deposit/address/list",
    
    # Withdrawals
    "withdraw_history": "/sapi/v1/capital/withdraw/history",
    
    # Account snapshots (daily snapshots for all account types)
    "account_snapshot": "/sapi/v1/accountSnapshot",
    
    # Transfers
    "universal_transfer": "/sapi/v1/asset/transfer",
    
    # Fees
    "trade_fee": "/sapi/v1/asset/tradeFee",
    
    # Dust (small balance conversions)
    "dust_log": "/sapi/v1/asset/dust",
    
    # === SPOT API ===
    # Account
    "spot_account": "/api/v3/account",
    "account_commission": "/api/v3/account/commission",
    "api_restrictions": "/sapi/v1/account/apiRestrictions",
    
    # Trading
    "spot_trades": "/api/v3/myTrades",
    "all_orders": "/api/v3/allOrders",
    
    # === MARGIN API ===
    # Cross Margin
    "margin_borrow_repay": "/sapi/v1/margin/borrow-repay",
    "margin_interest_history": "/sapi/v1/margin/interestHistory",
    "margin_force_liquidation": "/sapi/v1/margin/forceLiquidationRec",
    "margin_trades": "/sapi/v1/margin/myTrades",
    "margin_capital_flow": "/sapi/v1/margin/capital-flow",
    
    # Isolated Margin
    "isolated_margin_account": "/sapi/v1/margin/isolated/account",
    "isolated_margin_transfer": "/sapi/v1/margin/isolated/transfer",
    "isolated_margin_data": "/sapi/v1/margin/isolatedMarginData",
    
    # === FUTURES API (USDS) ===
    # Account
    "futures_account": "/fapi/v2/account",
    "futures_balance": "/fapi/v2/balance",
    "futures_position_risk": "/fapi/v2/positionRisk",
    "futures_position_risk_v3": "/fapi/v3/positionRisk",
    
    # Income (includes PnL, funding fees, commissions, rebates)
    "futures_income": "/fapi/v1/income",
    "futures_funding_rate": "/fapi/v1/fundingRate",
    "futures_position_margin_history": "/fapi/v1/positionMargin/history",
    
    # === SIMPLE EARN API ===
    # Flexible Products
    "earn_flexible_position": "/sapi/v1/simple-earn/flexible/position",
    "earn_flexible_rewards": "/sapi/v1/simple-earn/flexible/history/rewardsRecord",
    "earn_flexible_subscription": "/sapi/v1/simple-earn/flexible/history/subscriptionRecord",
    "earn_flexible_redemption": "/sapi/v1/simple-earn/flexible/history/redemptionRecord",
    "earn_flexible_rate_history": "/sapi/v1/simple-earn/flexible/history/rateHistory",
    
    # Locked Products
    "earn_locked_position": "/sapi/v1/simple-earn/locked/position",
    "earn_locked_rewards": "/sapi/v1/simple-earn/locked/history/rewardsRecord",
    "earn_locked_subscription": "/sapi/v1/simple-earn/locked/history/subscriptionRecord",
    "earn_locked_redemption": "/sapi/v1/simple-earn/locked/history/redemptionRecord",
    
    # === STAKING API ===
    # On-chain Yields
    "staking_position": "/sapi/v1/onchain-yields/locked/position",
    "staking_rewards": "/sapi/v1/onchain-yields/locked/history/rewardsRecord",
    "staking_subscription": "/sapi/v1/onchain-yields/locked/history/subscriptionRecord",
    "staking_redemption": "/sapi/v1/onchain-yields/locked/history/redemptionRecord",
    
    # SOL Staking
    "sol_staking_rewards": "/sapi/v1/sol-staking/sol/history/bnsolRewardsHistory",
    "sol_staking_boost_rewards": "/sapi/v1/sol-staking/sol/history/boostRewardsHistory",
    "sol_staking_redemption": "/sapi/v1/sol-staking/sol/history/redemptionHistory",
    
    # === SUB-ACCOUNT API ===
    "sub_account_list": "/sapi/v1/sub-account/list",
    "sub_account_assets": "/sapi/v1/sub-account/assets",
    "sub_account_transfer_history": "/sapi/v1/sub-account/transfer/subUserHistory",
    "sub_account_futures_transfer": "/sapi/v1/sub-account/futures/internalTransfer",
    "sub_account_universal_transfer": "/sapi/v1/sub-account/universalTransfer",
    
    # === REBATE API ===
    "rebate_history": "/sapi/v1/rebate/taxQuery",
    
    # === CONVERT API ===
    "convert_history": "/sapi/v1/convert/tradeFlow",
}

# Rate limits
RATE_LIMITS = {
    "default_weight": 1200,  # Per minute
    "order_weight": 10,      # Per second
    "raw_requests": 6100,    # Per 5 minutes
}

# Account types for account snapshot
ACCOUNT_SNAPSHOT_TYPES = ["SPOT", "MARGIN", "FUTURES"]

# Margin account types
MARGIN_TYPES = ["CROSS", "ISOLATED"]

# Futures income types
FUTURES_INCOME_TYPES = [
    "TRANSFER",           # Transfer
    "WELCOME_BONUS",      # Welcome bonus
    "REALIZED_PNL",       # Realized PnL
    "FUNDING_FEE",        # Funding fee
    "COMMISSION",         # Commission
    "INSURANCE_CLEAR",    # Insurance fund compensation
    "REFERRAL_KICKBACK",  # Referral kickback
    "COMMISSION_REBATE",  # Commission rebate
    "API_REBATE",         # API rebate
    "CONTEST_REWARD",     # Trading competition/tournament rewards
    "CROSS_COLLATERAL_TRANSFER",  # Cross-collateral transfer
    "OPTIONS_PREMIUM_FEE",        # Options premium fee
    "OPTIONS_SETTLE_PROFIT",      # Options settlement profit
    "INTERNAL_TRANSFER",          # Internal transfer
    "AUTO_EXCHANGE",              # Auto-exchange
    "DELIVERED_SETTELMENT",       # Delivered settlement
    "COIN_SWAP_DEPOSIT",          # Coin swap deposit
    "COIN_SWAP_WITHDRAW",         # Coin swap withdrawal
    "POSITION_LIMIT_INCREASE_FEE", # Position limit increase fee
]

# Universal transfer types
UNIVERSAL_TRANSFER_TYPES = {
    "MAIN_UMFUTURE": "Spot account to USD-M Futures account",
    "MAIN_CMFUTURE": "Spot account to COIN-M Futures account",
    "MAIN_MARGIN": "Spot account to Margin (cross) account",
    "UMFUTURE_MAIN": "USD-M Futures account to Spot account",
    "UMFUTURE_MARGIN": "USD-M Futures account to Margin (cross) account",
    "CMFUTURE_MAIN": "COIN-M Futures account to Spot account",
    "CMFUTURE_MARGIN": "COIN-M Futures account to Margin (cross) account",
    "MARGIN_MAIN": "Margin (cross) account to Spot account",
    "MARGIN_UMFUTURE": "Margin (cross) account to USD-M Futures account",
    "MARGIN_CMFUTURE": "Margin (cross) account to COIN-M Futures account",
    "ISOLATEDMARGIN_MARGIN": "Isolated margin account to Margin (cross) account",
    "MARGIN_ISOLATEDMARGIN": "Margin (cross) account to Isolated margin account",
    "ISOLATEDMARGIN_ISOLATEDMARGIN": "Isolated margin account to Isolated margin account",
    "MAIN_FUNDING": "Spot account to Funding account",
    "FUNDING_MAIN": "Funding account to Spot account",
    "FUNDING_UMFUTURE": "Funding account to USD-M Futures account",
    "UMFUTURE_FUNDING": "USD-M Futures account to Funding account",
    "MARGIN_FUNDING": "Margin (cross) account to Funding account",
    "FUNDING_MARGIN": "Funding account to Margin (cross) account",
    "FUNDING_CMFUTURE": "Funding account to COIN-M Futures account",
    "CMFUTURE_FUNDING": "COIN-M Futures account to Funding account",
}

# Max records per request
MAX_RECORDS = {
    "trades": 1000,
    "deposits": 1000,
    "withdrawals": 1000,
    "futures_income": 1000,
    "margin_trades": 1000,
    "convert_trades": 1000,
}

# Time constants
MAX_TIME_RANGE_DAYS = {
    "default": 90,
    "futures_income": 200,  # Futures income can go back 200 days
    "account_snapshot": 30,  # Account snapshot limited to 30 days
}