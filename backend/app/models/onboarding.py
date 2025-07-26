from enum import Enum
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class DataSourceType(str, Enum):
    BINANCE = "Binance"
    FIREBLOCKS = "Fireblocks"


class DataSource(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    type: DataSourceType
    api_key: str  # Encrypted
    api_secret: str  # Encrypted
    email: Optional[str] = Field(default=None, index=True)  # Sub-account email
    parent_id: Optional[int] = Field(default=None, foreign_key="datasource.id")  # Link to main account
    is_main_account: bool = Field(default=False)  # True for main/master accounts
    is_active: bool = Field(default=True)  # Enable/disable without deletion
    last_sync_at: Optional[datetime] = Field(default=None)  # Last sub-account sync check
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
