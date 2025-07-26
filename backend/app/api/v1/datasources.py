from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.db.session import get_session
from app.api.deps import get_current_user
from app.models.canonical import User
from app.models.onboarding import DataSourceType, DataSource
from app.schemas.datasource import DataSourceCreate, DataSourceResponse, SubAccountInfo, SubAccountCreate
from app.crud.datasource import create_data_source, get_datasource, get_datasources_by_user, delete_datasource
from app.crud.portfolio import get_portfolio
from app.core.security import decrypt, encrypt
from app.services.binance.client import BinanceAPIClient, BinanceAPIError, BinanceErrorType

router = APIRouter()

@router.post("/", response_model=DataSourceResponse)
def create_new_data_source(
    *,
    session: Session = Depends(get_session),
    datasource_in: DataSourceCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new data source (main account).
    For sub-accounts, use the /{id}/subaccounts endpoint.
    """
    portfolio = get_portfolio(session=session, portfolio_id=datasource_in.portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Create the datasource with additional fields
    datasource_dict = datasource_in.dict()
    datasource_dict["is_main_account"] = True
    datasource_dict["created_at"] = datetime.utcnow()
    datasource_dict["updated_at"] = datetime.utcnow()
    
    # Encrypt credentials
    datasource_dict["api_key"] = encrypt(datasource_dict["api_key"])
    datasource_dict["api_secret"] = encrypt(datasource_dict["api_secret"])
    
    # Create the datasource
    datasource = DataSource(**datasource_dict)
    session.add(datasource)
    session.commit()
    session.refresh(datasource)
    
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


@router.get("/{id}/subaccounts", response_model=List[SubAccountInfo])
def get_subaccounts(
    *,
    session: Session = Depends(get_session),
    id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get sub-accounts for a main account (Binance only).
    This endpoint fetches the list of sub-accounts from Binance API.
    """
    # Get the main account
    main_account = get_datasource(session=session, datasource_id=id)
    if not main_account:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Verify ownership
    portfolio = get_portfolio(session=session, portfolio_id=main_account.portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Only works for Binance
    if main_account.type != DataSourceType.BINANCE:
        raise HTTPException(status_code=400, detail="Sub-accounts are only supported for Binance")
    
    # Decrypt credentials
    api_key = decrypt(main_account.api_key)
    api_secret = decrypt(main_account.api_secret)
    
    try:
        # Create Binance client
        client = BinanceAPIClient(api_key=api_key, api_secret=api_secret)
        
        # Fetch sub-accounts
        response = client.get_sub_account_list(limit=200)
        
        # Get existing sub-accounts from database
        existing_subs = session.query(DataSource).filter(
            DataSource.parent_id == id,
            DataSource.type == DataSourceType.BINANCE
        ).all()
        existing_emails = {sub.email for sub in existing_subs}
        
        # Format response
        sub_accounts = []
        for sub in response.get("subAccounts", []):
            sub_email = sub.get("email", "")
            sub_accounts.append(SubAccountInfo(
                email=sub_email,
                is_freeze=sub.get("isFreeze", False),
                create_time=datetime.utcfromtimestamp(sub.get("createTime", 0) / 1000),
                is_configured=sub_email in existing_emails
            ))
        
        # Update last sync time
        main_account.last_sync_at = datetime.utcnow()
        session.add(main_account)
        session.commit()
        
        return sub_accounts
        
    except BinanceAPIError as e:
        if e.error_type == BinanceErrorType.API_KEY_INVALID:
            raise HTTPException(status_code=401, detail="This account is not a master account or API key is invalid")
        else:
            raise HTTPException(status_code=400, detail=f"Failed to fetch sub-accounts: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/{id}/subaccounts", response_model=DataSourceResponse)
def add_subaccount(
    *,
    session: Session = Depends(get_session),
    id: int,
    sub_account_in: SubAccountCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Add API credentials for a sub-account.
    """
    # Get the main account
    main_account = get_datasource(session=session, datasource_id=id)
    if not main_account:
        raise HTTPException(status_code=404, detail="Main account not found")
    
    # Verify ownership
    portfolio = get_portfolio(session=session, portfolio_id=main_account.portfolio_id, user=current_user)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if sub-account already exists
    existing_sub = session.query(DataSource).filter(
        DataSource.parent_id == id,
        DataSource.email == sub_account_in.email,
        DataSource.type == DataSourceType.BINANCE
    ).first()
    
    if existing_sub:
        # Update existing sub-account
        existing_sub.api_key = encrypt(sub_account_in.api_key)
        existing_sub.api_secret = encrypt(sub_account_in.api_secret)
        existing_sub.is_active = True
        existing_sub.updated_at = datetime.utcnow()
        session.add(existing_sub)
        session.commit()
        session.refresh(existing_sub)
        return existing_sub
    else:
        # Create new sub-account
        sub_account = DataSource(
            portfolio_id=main_account.portfolio_id,
            type=DataSourceType.BINANCE,
            api_key=encrypt(sub_account_in.api_key),
            api_secret=encrypt(sub_account_in.api_secret),
            email=sub_account_in.email,
            parent_id=id,
            is_main_account=False,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(sub_account)
        session.commit()
        session.refresh(sub_account)
        return sub_account
