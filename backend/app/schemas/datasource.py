from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.onboarding import DataSourceType

class DataSourceBase(BaseModel):
    type: DataSourceType
    api_key: str
    api_secret: str
    portfolio_id: int

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceResponse(BaseModel):
    id: int
    type: DataSourceType
    portfolio_id: int
    email: Optional[str] = None
    is_main_account: bool = False
    is_active: bool = True
    parent_id: Optional[int] = None

    class Config:
        orm_mode = True

class SubAccountInfo(BaseModel):
    """Information about a sub-account from Binance API"""
    email: str
    is_freeze: bool
    create_time: datetime
    is_configured: bool  # Whether API keys are stored in our database

class SubAccountCreate(BaseModel):
    """Schema for adding sub-account API credentials"""
    email: str
    api_key: str
    api_secret: str
