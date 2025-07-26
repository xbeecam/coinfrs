"""Add Binance reconciliation tables

Revision ID: 745089f4539e
Revises: a3c7d3af78e2
Create Date: 2025-07-26 21:22:16.514844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '745089f4539e'
down_revision: Union[str, Sequence[str], None] = 'a3c7d3af78e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create BinanceReconciliationTransfer table
    op.create_table('binancereconciliationtransfer',
        sa.Column('pid', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('fid', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('datetime', sa.DateTime(), nullable=False),
        sa.Column('txn_type', sa.String(length=50), nullable=False),
        sa.Column('txn_subtype', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('wallet', sa.String(length=20), nullable=False),
        sa.Column('asset', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('counter_party', sa.String(length=255), nullable=True),
        sa.Column('network', sa.String(length=50), nullable=True),
        sa.Column('txn_hash', sa.String(length=100), nullable=True),
        sa.Column('match_id', sa.Integer(), nullable=True),
        sa.Column('reconciled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("txn_type IN ('transfer_in', 'transfer_out', 'txn_fee')"),
        sa.CheckConstraint("wallet IN ('SPOT', 'MARGIN', 'FUTURES', 'OPTION')"),
        sa.PrimaryKeyConstraint('pid')
    )
    op.create_index(op.f('ix_binancereconciliationtransfer_asset'), 'binancereconciliationtransfer', ['asset'], unique=False)
    op.create_index(op.f('ix_binancereconciliationtransfer_email'), 'binancereconciliationtransfer', ['email'], unique=False)
    op.create_index(op.f('ix_binancereconciliationtransfer_datetime'), 'binancereconciliationtransfer', ['datetime'], unique=False)
    op.create_index('ix_binancereconciliationtransfer_source_external_id', 'binancereconciliationtransfer', ['source', 'external_id'], unique=True)

    # Create BinanceReconciliationTrade table
    op.create_table('binancereconciliationtrade',
        sa.Column('pid', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('fid', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('datetime', sa.DateTime(), nullable=False),
        sa.Column('txn_type', sa.String(length=50), nullable=False),
        sa.Column('txn_subtype', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('wallet', sa.String(length=20), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('asset', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('agg_id', sa.Integer(), nullable=True),
        sa.Column('reconciled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("txn_subtype IN ('spot_buy', 'spot_sell', 'maker_fee', 'taker_fee', 'convert_buy', 'convert_sell')"),
        sa.PrimaryKeyConstraint('pid')
    )
    op.create_index(op.f('ix_binancereconciliationtrade_asset'), 'binancereconciliationtrade', ['asset'], unique=False)
    op.create_index(op.f('ix_binancereconciliationtrade_email'), 'binancereconciliationtrade', ['email'], unique=False)
    op.create_index(op.f('ix_binancereconciliationtrade_symbol'), 'binancereconciliationtrade', ['symbol'], unique=False)
    op.create_index(op.f('ix_binancereconciliationtrade_datetime'), 'binancereconciliationtrade', ['datetime'], unique=False)
    op.create_index('ix_binancereconciliationtrade_source_external_id', 'binancereconciliationtrade', ['source', 'external_id'], unique=True)

    # Create BinanceReconciliationBalance table
    op.create_table('binancereconciliationbalance',
        sa.Column('pid', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('fid', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('wallet', sa.String(length=20), nullable=False),
        sa.Column('asset', sa.String(length=20), nullable=False),
        sa.Column('raw_balance', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('raw_loan', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('raw_interest', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('raw_unrealised_pnl', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('cal_balance', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('cal_loan', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('cal_interest', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('cal_unrealised_pnl', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('variance_in_asset', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('variance_in_usd', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('usd_price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("wallet IN ('SPOT', 'MARGIN', 'FUTURES', 'OPTION')"),
        sa.PrimaryKeyConstraint('pid')
    )
    op.create_index(op.f('ix_binancereconciliationbalance_asset'), 'binancereconciliationbalance', ['asset'], unique=False)
    op.create_index(op.f('ix_binancereconciliationbalance_date'), 'binancereconciliationbalance', ['date'], unique=False)
    op.create_index(op.f('ix_binancereconciliationbalance_email'), 'binancereconciliationbalance', ['email'], unique=False)
    op.create_index('ix_binancereconciliationbalance_email_date_wallet_asset', 'binancereconciliationbalance', ['email', 'date', 'wallet', 'asset'], unique=True)

    # Create BinanceExchangeInfo table
    op.create_table('binanceexchangeinfo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('base_asset', sa.String(length=20), nullable=False),
        sa.Column('quote_asset', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_spot_trading_allowed', sa.Boolean(), nullable=False),
        sa.Column('is_margin_trading_allowed', sa.Boolean(), nullable=False),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )
    op.create_index(op.f('ix_binanceexchangeinfo_base_asset'), 'binanceexchangeinfo', ['base_asset'], unique=False)
    op.create_index(op.f('ix_binanceexchangeinfo_quote_asset'), 'binanceexchangeinfo', ['quote_asset'], unique=False)

    # Create BinanceTradedSymbols table
    op.create_table('binancetradedsymbols',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('last_trade_time', sa.DateTime(), nullable=False),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_checked', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', 'symbol')
    )

    # Create BinanceReconciliationError table
    op.create_table('binancereconciliationerror',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('error_type', sa.String(length=50), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('raw_error', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('needs_manual_review', sa.Boolean(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create raw data tables
    op.create_table('binancerawdailysnapshot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('snapshot_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binancerawdailysnapshot_email'), 'binancerawdailysnapshot', ['email'], unique=False)

    op.create_table('binancerawdeposithistory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('deposit_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binancerawdeposithistory_email'), 'binancerawdeposithistory', ['email'], unique=False)

    op.create_table('binancerawwithdrawhistory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('withdraw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binancerawwithdrawhistory_email'), 'binancerawwithdrawhistory', ['email'], unique=False)

    op.create_table('binancerawtransferbetweenaccountmainspot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('transfer_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binancerawtransferbetweenaccountmainspot_email'), 'binancerawtransferbetweenaccountmainspot', ['email'], unique=False)

    op.create_table('binancerawtransferbetweenaccountsub',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('transfer_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binancerawtransferbetweenaccountsub_email'), 'binancerawtransferbetweenaccountsub', ['email'], unique=False)

    op.create_table('binancerawtransferbetweenwallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('transfer_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binancerawtransferbetweenwallets_email'), 'binancerawtransferbetweenwallets', ['email'], unique=False)

    op.create_table('binancerawtrades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('trade_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binancerawtrades_email'), 'binancerawtrades', ['email'], unique=False)
    op.create_index(op.f('ix_binancerawtrades_symbol'), 'binancerawtrades', ['symbol'], unique=False)

    op.create_table('binancerawconverthistory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('convert_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binancerawconverthistory_email'), 'binancerawconverthistory', ['email'], unique=False)

    # Create the view
    op.execute("""
        CREATE VIEW v_binance_user_assets AS
        SELECT DISTINCT 
            email,
            asset,
            MAX(last_seen) as last_seen
        FROM (
            SELECT email, asset, datetime as last_seen
            FROM binancereconciliationtransfer
            UNION ALL
            SELECT email, asset, datetime as last_seen
            FROM binancereconciliationtrade
            UNION ALL
            SELECT email, asset, date as last_seen
            FROM binancereconciliationbalance
            WHERE raw_balance > 0 OR cal_balance > 0
        ) AS all_assets
        GROUP BY email, asset
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the view first
    op.execute("DROP VIEW IF EXISTS v_binance_user_assets")

    # Drop raw data tables
    op.drop_index(op.f('ix_binancerawconverthistory_email'), table_name='binancerawconverthistory')
    op.drop_table('binancerawconverthistory')
    
    op.drop_index(op.f('ix_binancerawtrades_symbol'), table_name='binancerawtrades')
    op.drop_index(op.f('ix_binancerawtrades_email'), table_name='binancerawtrades')
    op.drop_table('binancerawtrades')
    
    op.drop_index(op.f('ix_binancerawtransferbetweenwallets_email'), table_name='binancerawtransferbetweenwallets')
    op.drop_table('binancerawtransferbetweenwallets')
    
    op.drop_index(op.f('ix_binancerawtransferbetweenaccountsub_email'), table_name='binancerawtransferbetweenaccountsub')
    op.drop_table('binancerawtransferbetweenaccountsub')
    
    op.drop_index(op.f('ix_binancerawtransferbetweenaccountmainspot_email'), table_name='binancerawtransferbetweenaccountmainspot')
    op.drop_table('binancerawtransferbetweenaccountmainspot')
    
    op.drop_index(op.f('ix_binancerawwithdrawhistory_email'), table_name='binancerawwithdrawhistory')
    op.drop_table('binancerawwithdrawhistory')
    
    op.drop_index(op.f('ix_binancerawdeposithistory_email'), table_name='binancerawdeposithistory')
    op.drop_table('binancerawdeposithistory')
    
    op.drop_index(op.f('ix_binancerawdailysnapshot_email'), table_name='binancerawdailysnapshot')
    op.drop_table('binancerawdailysnapshot')

    # Drop reconciliation tables
    op.drop_table('binancereconciliationerror')
    op.drop_table('binancetradedsymbols')
    
    op.drop_index(op.f('ix_binanceexchangeinfo_quote_asset'), table_name='binanceexchangeinfo')
    op.drop_index(op.f('ix_binanceexchangeinfo_base_asset'), table_name='binanceexchangeinfo')
    op.drop_table('binanceexchangeinfo')
    
    op.drop_index('ix_binancereconciliationbalance_email_date_wallet_asset', table_name='binancereconciliationbalance')
    op.drop_index(op.f('ix_binancereconciliationbalance_email'), table_name='binancereconciliationbalance')
    op.drop_index(op.f('ix_binancereconciliationbalance_date'), table_name='binancereconciliationbalance')
    op.drop_index(op.f('ix_binancereconciliationbalance_asset'), table_name='binancereconciliationbalance')
    op.drop_table('binancereconciliationbalance')
    
    op.drop_index('ix_binancereconciliationtrade_source_external_id', table_name='binancereconciliationtrade')
    op.drop_index(op.f('ix_binancereconciliationtrade_datetime'), table_name='binancereconciliationtrade')
    op.drop_index(op.f('ix_binancereconciliationtrade_symbol'), table_name='binancereconciliationtrade')
    op.drop_index(op.f('ix_binancereconciliationtrade_email'), table_name='binancereconciliationtrade')
    op.drop_index(op.f('ix_binancereconciliationtrade_asset'), table_name='binancereconciliationtrade')
    op.drop_table('binancereconciliationtrade')
    
    op.drop_index('ix_binancereconciliationtransfer_source_external_id', table_name='binancereconciliationtransfer')
    op.drop_index(op.f('ix_binancereconciliationtransfer_datetime'), table_name='binancereconciliationtransfer')
    op.drop_index(op.f('ix_binancereconciliationtransfer_email'), table_name='binancereconciliationtransfer')
    op.drop_index(op.f('ix_binancereconciliationtransfer_asset'), table_name='binancereconciliationtransfer')
    op.drop_table('binancereconciliationtransfer')