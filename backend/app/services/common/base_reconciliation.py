from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import logging


class ReconciliationResult:
    """Container for reconciliation results."""
    def __init__(self):
        self.discrepancies: List[Dict[str, Any]] = []
        self.reconciled_accounts: int = 0
        self.failed_accounts: int = 0
        self.total_discrepancy_value: Decimal = Decimal('0')
        self.timestamp: datetime = datetime.utcnow()
        
    def add_discrepancy(self, account: str, asset: str, expected: Decimal, actual: Decimal):
        """Add a discrepancy to the results."""
        self.discrepancies.append({
            'account': account,
            'asset': asset,
            'expected': expected,
            'actual': actual,
            'difference': actual - expected,
            'timestamp': datetime.utcnow()
        })


class BaseReconciliationService(ABC):
    """
    Abstract base class for reconciliation services.
    Implements the daily completeness check: Position(T-2) + Transactions = Position(T-1)
    """
    
    def __init__(self, data_source_id: int):
        self.data_source_id = data_source_id
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def fetch_position_snapshot(
        self, 
        snapshot_date: date,
        account_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Fetch position snapshot for a specific date.
        
        Args:
            snapshot_date: Date of the snapshot
            account_type: Optional filter for account type
            
        Returns:
            Dict mapping account_id -> asset -> amount
        """
        pass
    
    @abstractmethod
    async def fetch_transactions_between(
        self,
        start_date: date,
        end_date: date,
        account_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all transactions between two dates.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            account_type: Optional filter for account type
            
        Returns:
            List of transactions
        """
        pass
    
    @abstractmethod
    async def calculate_expected_position(
        self,
        starting_position: Dict[str, Decimal],
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Decimal]:
        """
        Calculate expected position based on starting position and transactions.
        
        Args:
            starting_position: Starting balances by asset
            transactions: List of transactions to apply
            
        Returns:
            Expected final position
        """
        pass
    
    async def reconcile_daily(
        self,
        reconciliation_date: date,
        account_types: Optional[List[str]] = None
    ) -> ReconciliationResult:
        """
        Perform daily reconciliation for the specified date.
        Checks: Position(T-2) + Transactions = Position(T-1)
        
        Args:
            reconciliation_date: The T-1 date to reconcile
            account_types: Optional list of account types to check
            
        Returns:
            ReconciliationResult with all discrepancies
        """
        result = ReconciliationResult()
        t_minus_2 = reconciliation_date.replace(day=reconciliation_date.day - 2)
        t_minus_1 = reconciliation_date.replace(day=reconciliation_date.day - 1)
        
        try:
            # Fetch positions for T-2 and T-1
            positions_t2 = await self.fetch_position_snapshot(t_minus_2)
            positions_t1 = await self.fetch_position_snapshot(t_minus_1)
            
            # Fetch transactions between T-2 and T-1
            transactions = await self.fetch_transactions_between(t_minus_2, t_minus_1)
            
            # Reconcile each account
            all_accounts = set(positions_t2.keys()) | set(positions_t1.keys())
            
            for account_id in all_accounts:
                try:
                    start_pos = positions_t2.get(account_id, {})
                    actual_pos = positions_t1.get(account_id, {})
                    
                    # Filter transactions for this account
                    account_txns = [t for t in transactions if t.get('account_id') == account_id]
                    
                    # Calculate expected position
                    expected_pos = await self.calculate_expected_position(start_pos, account_txns)
                    
                    # Compare positions
                    all_assets = set(expected_pos.keys()) | set(actual_pos.keys())
                    
                    for asset in all_assets:
                        expected = expected_pos.get(asset, Decimal('0'))
                        actual = actual_pos.get(asset, Decimal('0'))
                        
                        # Check for discrepancies (with small tolerance for rounding)
                        tolerance = Decimal('0.00000001')
                        if abs(expected - actual) > tolerance:
                            result.add_discrepancy(account_id, asset, expected, actual)
                    
                    result.reconciled_accounts += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to reconcile account {account_id}: {e}")
                    result.failed_accounts += 1
            
            # Calculate total discrepancy value (would need price data in real implementation)
            # For now, just count the number of discrepancies
            
            return result
            
        except Exception as e:
            self.logger.error(f"Reconciliation failed: {e}")
            raise
    
    @abstractmethod
    async def generate_alerts(self, result: ReconciliationResult):
        """Generate alerts for any discrepancies found."""
        pass