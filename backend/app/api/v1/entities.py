from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.db.session import get_session
from app.api.deps import get_current_user
from app.models.canonical import User, Entity
from app.schemas.entity import EntityCreate, EntityResponse, EntityUpdate
from app.crud.entity import create_entity, get_entities_by_portfolio, get_entity, update_entity, delete_entity
from app.crud.portfolio import get_portfolio

router = APIRouter()

@router.post("/portfolios/{portfolio_id}/entities", response_model=EntityResponse)
def create_new_entity(
    *,
    session: Session = Depends(get_session),
    portfolio_id: int,
    entity_in: EntityCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new entity for a portfolio.
    """
    portfolio = get_portfolio(session=session, portfolio_id=portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    entity = create_entity(session=session, entity_in=entity_in, portfolio=portfolio)
    return entity

@router.get("/portfolios/{portfolio_id}/entities", response_model=List[EntityResponse])
def read_entities(
    *,
    session: Session = Depends(get_session),
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve entities for a portfolio.
    """
    portfolio = get_portfolio(session=session, portfolio_id=portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return get_entities_by_portfolio(session=session, portfolio=portfolio)

@router.get("/portfolios/{portfolio_id}/entities/{entity_id}", response_model=EntityResponse)
def read_entity(
    *,
    session: Session = Depends(get_session),
    portfolio_id: int,
    entity_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get entity by ID.
    """
    portfolio = get_portfolio(session=session, portfolio_id=portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    entity = get_entity(session=session, entity_id=entity_id, portfolio=portfolio)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity

@router.put("/portfolios/{portfolio_id}/entities/{entity_id}", response_model=EntityResponse)
def update_existing_entity(
    *,
    session: Session = Depends(get_session),
    portfolio_id: int,
    entity_id: int,
    entity_in: EntityUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update an entity.
    """
    portfolio = get_portfolio(session=session, portfolio_id=portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db_entity = get_entity(session=session, entity_id=entity_id, portfolio=portfolio)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    entity = update_entity(session=session, db_entity=db_entity, entity_in=entity_in)
    return entity

@router.delete("/portfolios/{portfolio_id}/entities/{entity_id}", response_model=EntityResponse)
def delete_existing_entity(
    *,
    session: Session = Depends(get_session),
    portfolio_id: int,
    entity_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete an entity.
    """
    portfolio = get_portfolio(session=session, portfolio_id=portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db_entity = get_entity(session=session, entity_id=entity_id, portfolio=portfolio)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    delete_entity(session=session, db_entity=db_entity)
    return db_entity
