from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
import datetime as dt
from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


class TransactionType(str, Enum):
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    TXN_FEE = "txn_fee"
    TRADE = "trade"


class TransactionSubtype(str, Enum):
    # Transfer subtypes
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    WITHDRAWAL_FEE = "withdrawal_fee"
    TRANSFER_BETWEEN_ACCOUNT_MAIN_SPOT = "transfer_between_account_main_spot"
    TRANSFER_BETWEEN_ACCOUNT_SUB = "transfer_between_account_sub"
    TRANSFER_BETWEEN_WALLETS = "transfer_between_wallets"
    
    # Trade subtypes
    SPOT_BUY = "spot_buy"
    SPOT_SELL = "spot_sell"
    MAKER_FEE = "maker_fee"
    TAKER_FEE = "taker_fee"
    CONVERT_BUY = "convert_buy"
    CONVERT_SELL = "convert_sell"


class WalletType(str, Enum):
    SPOT = "SPOT"
    MARGIN = "MARGIN"
    FUTURES = "FUTURES"
    OPTION = "OPTION"


class BinanceReconciliationTransfer(SQLModel, table=True):
    """Reconciliation table for all transfer transactions"""
    pid: int = Field(default=None, primary_key=True)
    source: str = Field(max_length=100)
    fid: int
    external_id: str = Field(max_length=100)
    datetime: datetime
    txn_type: str = Field(max_length=50)
    txn_subtype: str = Field(max_length=100)
    email: str = Field(max_length=255, index=True)
    wallet: str = Field(max_length=20)
    asset: str = Field(max_length=20, index=True)
    amount: Decimal = Field(max_digits=36, decimal_places=18)
    counter_party: Optional[str] = Field(default=None, max_length=255)
    network: Optional[str] = Field(default=None, max_length=50)
    txn_hash: Optional[str] = Field(default=None, max_length=100)
    match_id: Optional[int] = Field(default=None)
    reconciled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceReconciliationTrade(SQLModel, table=True):
    """Reconciliation table for all trade transactions"""
    pid: int = Field(default=None, primary_key=True)
    source: str = Field(max_length=100)
    fid: int
    external_id: str = Field(max_length=100)
    datetime: datetime
    txn_type: str = Field(default="trade", max_length=50)
    txn_subtype: str = Field(max_length=50)
    email: str = Field(max_length=255, index=True)
    wallet: str = Field(default="SPOT", max_length=20)
    symbol: str = Field(max_length=20, index=True)
    asset: str = Field(max_length=20, index=True)
    amount: Decimal = Field(max_digits=36, decimal_places=18)
    price: Optional[Decimal] = Field(default=None, max_digits=36, decimal_places=18)
    agg_id: Optional[int] = Field(default=None)
    reconciled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceReconciliationBalance(SQLModel, table=True):
    """Daily balance snapshots for reconciliation"""
    pid: int = Field(default=None, primary_key=True)
    source: str = Field(max_length=100)
    fid: int
    external_id: Optional[str] = Field(default=None, max_length=100)
    date: dt.date = Field(index=True)
    email: str = Field(max_length=255, index=True)
    wallet: str = Field(max_length=20)
    asset: str = Field(max_length=20, index=True)
    raw_balance: Decimal = Field(default=0, max_digits=36, decimal_places=18)
    raw_loan: Decimal = Field(default=0, max_digits=36, decimal_places=18)
    raw_interest: Decimal = Field(default=0, max_digits=36, decimal_places=18)
    raw_unrealised_pnl: Decimal = Field(default=0, max_digits=36, decimal_places=18)
    cal_balance: Optional[Decimal] = Field(default=None, max_digits=36, decimal_places=18)
    cal_loan: Optional[Decimal] = Field(default=None, max_digits=36, decimal_places=18)
    cal_interest: Optional[Decimal] = Field(default=None, max_digits=36, decimal_places=18)
    cal_unrealised_pnl: Optional[Decimal] = Field(default=None, max_digits=36, decimal_places=18)
    variance_in_asset: Optional[Decimal] = Field(default=None, max_digits=36, decimal_places=18)
    variance_in_usd: Optional[Decimal] = Field(default=None, max_digits=36, decimal_places=18)
    usd_price: Optional[Decimal] = Field(default=None, max_digits=36, decimal_places=18)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceExchangeInfo(SQLModel, table=True):
    """Exchange information cache for symbol details"""
    id: int = Field(default=None, primary_key=True)
    symbol: str = Field(max_length=20, unique=True)
    base_asset: str = Field(max_length=20, index=True)
    quote_asset: str = Field(max_length=20, index=True)
    status: str = Field(max_length=20)
    is_spot_trading_allowed: bool
    is_margin_trading_allowed: bool
    raw_data: dict = Field(sa_column=sa.Column(JSONB))
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceTradedSymbols(SQLModel, table=True):
    """Track which symbols have been traded by each user"""
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=255)
    symbol: str = Field(max_length=20)
    last_trade_time: datetime
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    class Config:
        arbitrary_types_allowed = True


class BinanceReconciliationError(SQLModel, table=True):
    """Error tracking for reconciliation process"""
    id: int = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    email: Optional[str] = Field(default=None, max_length=255)
    error_type: str = Field(max_length=50)
    symbol: Optional[str] = Field(default=None, max_length=20)
    error_message: str
    raw_error: Optional[dict] = Field(default=None, sa_column=sa.Column(JSONB))
    needs_manual_review: bool = Field(default=False)
    resolved_at: Optional[datetime] = Field(default=None)
    resolution_notes: Optional[str] = Field(default=None)


# Raw data tables for audit trail
class BinanceRawDailySnapshot(SQLModel, table=True):
    """Raw daily snapshot data from Binance API"""
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, index=True)
    snapshot_data: dict = Field(sa_column=sa.Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceRawDepositHistory(SQLModel, table=True):
    """Raw deposit history data from Binance API"""
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, index=True)
    deposit_data: dict = Field(sa_column=sa.Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceRawWithdrawHistory(SQLModel, table=True):
    """Raw withdrawal history data from Binance API"""
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, index=True)
    withdraw_data: dict = Field(sa_column=sa.Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceRawTransferBetweenAccountMainSpot(SQLModel, table=True):
    """Raw transfer data between main and sub accounts (main perspective)"""
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, index=True)
    transfer_data: dict = Field(sa_column=sa.Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceRawTransferBetweenAccountSub(SQLModel, table=True):
    """Raw transfer data between main and sub accounts (sub perspective)"""
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, index=True)
    transfer_data: dict = Field(sa_column=sa.Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceRawTransferBetweenWallets(SQLModel, table=True):
    """Raw transfer data between different wallet types"""
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, index=True)
    transfer_data: dict = Field(sa_column=sa.Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceRawTrades(SQLModel, table=True):
    """Raw trade data from Binance API"""
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, index=True)
    symbol: str = Field(max_length=20, index=True)
    trade_data: dict = Field(sa_column=sa.Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BinanceRawConvertHistory(SQLModel, table=True):
    """Raw convert transaction data from Binance API"""
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, index=True)
    convert_data: dict = Field(sa_column=sa.Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)