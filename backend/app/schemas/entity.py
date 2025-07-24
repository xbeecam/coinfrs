from pydantic import BaseModel

class EntityBase(BaseModel):
    name: str

class EntityCreate(EntityBase):
    pass

class EntityUpdate(EntityBase):
    pass

class EntityResponse(EntityBase):
    id: int
    portfolio_id: int

    class Config:
        orm_mode = True
