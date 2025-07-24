from typing import List
from sqlmodel import Session, select
from app.models.canonical import Entity, Portfolio
from app.schemas.entity import EntityCreate, EntityUpdate

def get_entity(session: Session, *, entity_id: int, portfolio: Portfolio) -> Entity | None:
    statement = select(Entity).where(Entity.id == entity_id, Entity.portfolio_id == portfolio.id)
    return session.exec(statement).first()

def get_entities_by_portfolio(session: Session, *, portfolio: Portfolio) -> List[Entity]:
    statement = select(Entity).where(Entity.portfolio_id == portfolio.id)
    return session.exec(statement).all()

def create_entity(session: Session, *, entity_in: EntityCreate, portfolio: Portfolio) -> Entity:
    db_entity = Entity.from_orm(entity_in, update={'portfolio_id': portfolio.id})
    session.add(db_entity)
    session.commit()
    session.refresh(db_entity)
    return db_entity

def update_entity(session: Session, *, db_entity: Entity, entity_in: EntityUpdate) -> Entity:
    entity_data = entity_in.dict(exclude_unset=True)
    for key, value in entity_data.items():
        setattr(db_entity, key, value)
    session.add(db_entity)
    session.commit()
    session.refresh(db_entity)
    return db_entity

def delete_entity(session: Session, *, db_entity: Entity):
    session.delete(db_entity)
    session.commit()
