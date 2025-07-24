from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import uuid as uuid_lib


class BaseModel(SQLModel):
    """Base model with common fields for all database models."""
    
    id: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    created_by: Optional[uuid_lib.UUID] = Field(default=None, foreign_key="user.id")
    updated_by: Optional[uuid_lib.UUID] = Field(default=None, foreign_key="user.id")
    deleted_at: Optional[datetime] = Field(default=None)
    
    class Config:
        # Allow UUID serialization
        json_encoders = {
            uuid_lib.UUID: lambda v: str(v),
        }