from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.db.session import get_session
from app.api.deps import get_current_user
from app.models.canonical import User, Portfolio
from app.schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioUpdate
from app.crud.portfolio import create_portfolio, get_portfolios_by_user, get_portfolio, update_portfolio, delete_portfolio

router = APIRouter()

@router.post("/", response_model=PortfolioResponse)
def create_new_portfolio(
    *,
    session: Session = Depends(get_session),
    portfolio_in: PortfolioCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new portfolio.
    """
    portfolio = create_portfolio(session=session, portfolio_in=portfolio_in, user=current_user)
    return portfolio

@router.get("/", response_model=List[PortfolioResponse])
def read_portfolios(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve portfolios for the current user.
    """
    return get_portfolios_by_user(session=session, user=current_user)

@router.get("/{id}", response_model=PortfolioResponse)
def read_portfolio(
    *,
    session: Session = Depends(get_session),
    id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get portfolio by ID.
    """
    portfolio = get_portfolio(session=session, portfolio_id=id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.put("/{id}", response_model=PortfolioResponse)
def update_existing_portfolio(
    *,
    session: Session = Depends(get_session),
    id: int,
    portfolio_in: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update a portfolio.
    """
    db_portfolio = get_portfolio(session=session, portfolio_id=id, user=current_user)
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    portfolio = update_portfolio(session=session, db_portfolio=db_portfolio, portfolio_in=portfolio_in)
    return portfolio

@router.delete("/{id}", response_model=PortfolioResponse)
def delete_existing_portfolio(
    *,
    session: Session = Depends(get_session),
    id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a portfolio.
    """
    db_portfolio = get_portfolio(session=session, portfolio_id=id, user=current_user)
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    delete_portfolio(session=session, db_portfolio=db_portfolio)
    return db_portfolio
