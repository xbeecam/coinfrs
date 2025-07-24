from pydantic import BaseModel
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

    class Config:
        orm_mode = True
