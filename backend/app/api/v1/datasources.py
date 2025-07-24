from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.db.session import get_session
from app.api.deps import get_current_user
from app.models.canonical import User
from app.models.onboarding import DataSourceType
from app.schemas.datasource import DataSourceCreate, DataSourceResponse
from app.crud.datasource import create_data_source, get_datasource, get_datasources_by_user, delete_datasource
from app.crud.portfolio import get_portfolio
from app.core.security import decrypt
from app.services.binance.client import BinanceAPIClient

router = APIRouter()

@router.post("/", response_model=DataSourceResponse)
def create_new_data_source(
    *,
    session: Session = Depends(get_session),
    datasource_in: DataSourceCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new data source.
    """
    portfolio = get_portfolio(session=session, portfolio_id=datasource_in.portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    datasource = create_data_source(session=session, datasource_in=datasource_in)
    return datasource

@router.get("/", response_model=List[DataSourceResponse])
def read_datasources(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve data sources for the current user.
    """
    return get_datasources_by_user(session=session, user=current_user)

@router.delete("/{id}", response_model=DataSourceResponse)
def delete_existing_datasource(
    *,
    session: Session = Depends(get_session),
    id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a data source.
    """
    db_datasource = get_datasource(session=session, datasource_id=id)
    if not db_datasource:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    portfolio = get_portfolio(session=session, portfolio_id=db_datasource.portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    delete_datasource(session=session, db_datasource=db_datasource)
    return db_datasource

@router.post("/{id}/validate", response_model=bool)
def validate_data_source(
    *,
    session: Session = Depends(get_session),
    id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Validate API credentials for a data source.
    """
    db_datasource = get_datasource(session=session, datasource_id=id)
    if not db_datasource:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    portfolio = get_portfolio(session=session, portfolio_id=db_datasource.portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    api_key = decrypt(db_datasource.api_key)
    api_secret = decrypt(db_datasource.api_secret)

    if db_datasource.type == DataSourceType.BINANCE:
        client = BinanceAPIClient(api_key=api_key, api_secret=api_secret)
        is_valid = client.validate_api_permissions()
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid API credentials or permissions.")
    else:
        raise HTTPException(status_code=400, detail="Validation for this source type is not implemented.")

    return is_valid
