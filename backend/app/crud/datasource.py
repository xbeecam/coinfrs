from typing import List
from sqlmodel import Session, select
from app.models.onboarding import DataSource
from app.models.canonical import User, Portfolio
from app.schemas.datasource import DataSourceCreate
from app.core.security import encrypt

def get_datasource(session: Session, *, datasource_id: int) -> DataSource | None:
    statement = select(DataSource).where(DataSource.id == datasource_id)
    return session.exec(statement).first()

def get_datasources_by_user(session: Session, *, user: User) -> List[DataSource]:
    statement = select(DataSource).join(Portfolio).where(Portfolio.user_id == user.id)
    return session.exec(statement).all()

def create_data_source(session: Session, *, datasource_in: DataSourceCreate) -> DataSource:
    encrypted_api_key = encrypt(datasource_in.api_key)
    encrypted_api_secret = encrypt(datasource_in.api_secret)
    
    db_datasource = DataSource(
        type=datasource_in.type,
        api_key=encrypted_api_key,
        api_secret=encrypted_api_secret,
        portfolio_id=datasource_in.portfolio_id,
    )
    
    session.add(db_datasource)
    session.commit()
    session.refresh(db_datasource)
    return db_datasource

def delete_datasource(session: Session, *, db_datasource: DataSource):
    session.delete(db_datasource)
    session.commit()
