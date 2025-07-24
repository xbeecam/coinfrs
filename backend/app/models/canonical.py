from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from decimal import Decimal


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRADE = "trade"


class TransactionStatus(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: Optional[str] = Field(default=None)
    google_auth_id: Optional[str] = Field(default=None, unique=True)
    is_active: bool = Field(default=True)


class Portfolio(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="user.id")


class Entity(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    portfolio_id: int = Field(foreign_key="portfolio.id")


class Transaction(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="rawbinancedata.id")  # This will need to be more generic
    timestamp: datetime
    asset: str
    amount: Decimal
    type: TransactionType
    status: TransactionStatus
