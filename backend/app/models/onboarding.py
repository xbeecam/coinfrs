from enum import Enum
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
