from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    ERROR = "error"


class RawBinanceData(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    source_raw_id: str = Field(index=True)
    raw_payload: dict = Field(sa_column=sa.Column(JSONB))
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING, index=True
    )


class RawFireblocksData(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    source_raw_id: str = Field(index=True)
    raw_payload: dict = Field(sa_column=sa.Column(JSONB))
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING, index=True
    )


class BinanceAccountType(str, Enum):
    SPOT = "spot"
    MARGIN = "margin"
    FUTURES = "futures"


class RawBinancePositionSnapshot(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    data_source_id: int = Field(foreign_key="datasource.id", index=True)
    account_type: BinanceAccountType = Field(index=True)
    sub_account_id: Optional[str] = Field(default=None, index=True)
    snapshot_timestamp: datetime = Field(index=True)
    balances: dict = Field(sa_column=sa.Column(JSONB))
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class RawFireblocksPositionSnapshot(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    data_source_id: int = Field(foreign_key="datasource.id", index=True)
    vault_id: str = Field(index=True)
    vault_name: Optional[str] = Field(default=None)
    snapshot_timestamp: datetime = Field(index=True)
    balances: dict = Field(sa_column=sa.Column(JSONB))
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
