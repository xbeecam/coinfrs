from typing import List
from sqlmodel import Session, select
from app.models.canonical import Portfolio, User
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate

def get_portfolio(session: Session, *, portfolio_id: int, user: User) -> Portfolio | None:
    statement = select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
    return session.exec(statement).first()

def get_portfolios_by_user(session: Session, *, user: User) -> List[Portfolio]:
    statement = select(Portfolio).where(Portfolio.user_id == user.id)
    return session.exec(statement).all()

def create_portfolio(session: Session, *, portfolio_in: PortfolioCreate, user: User) -> Portfolio:
    db_portfolio = Portfolio.from_orm(portfolio_in, update={'user_id': user.id})
    session.add(db_portfolio)
    session.commit()
    session.refresh(db_portfolio)
    return db_portfolio

def update_portfolio(session: Session, *, db_portfolio: Portfolio, portfolio_in: PortfolioUpdate) -> Portfolio:
    portfolio_data = portfolio_in.dict(exclude_unset=True)
    for key, value in portfolio_data.items():
        setattr(db_portfolio, key, value)
    session.add(db_portfolio)
    session.commit()
    session.refresh(db_portfolio)
    return db_portfolio

def delete_portfolio(session: Session, *, db_portfolio: Portfolio):
    session.delete(db_portfolio)
    session.commit()
