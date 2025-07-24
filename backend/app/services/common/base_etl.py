from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from app.models.staging import ProcessingStatus


class BaseETLService(ABC):
    """
    Abstract base class for ETL (Extract, Transform, Load) services.
    Handles transformation from staging layer to canonical layer.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def extract_unprocessed_records(
        self, 
        batch_size: int = 1000,
        record_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract unprocessed records from the staging layer.
        
        Args:
            batch_size: Maximum number of records to process
            record_type: Optional filter for specific record types
            
        Returns:
            List of raw records to process
        """
        pass
    
    @abstractmethod
    async def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single raw record to canonical format.
        
        Args:
            raw_record: Raw record from staging layer
            
        Returns:
            Transformed record ready for canonical layer
        """
        pass
    
    @abstractmethod
    async def load_to_canonical(self, transformed_records: List[Dict[str, Any]]):
        """
        Load transformed records into the canonical layer.
        
        Args:
            transformed_records: List of transformed records
        """
        pass
    
    @abstractmethod
    async def update_processing_status(
        self, 
        record_ids: List[int], 
        status: ProcessingStatus,
        error_message: Optional[str] = None
    ):
        """
        Update the processing status of records in staging layer.
        
        Args:
            record_ids: List of record IDs to update
            status: New processing status
            error_message: Optional error message for failed records
        """
        pass
    
    async def process_batch(self, batch_size: int = 1000) -> Dict[str, int]:
        """
        Process a batch of records through the ETL pipeline.
        
        Args:
            batch_size: Number of records to process
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'extracted': 0,
            'transformed': 0,
            'loaded': 0,
            'errors': 0
        }
        
        try:
            # Extract
            raw_records = await self.extract_unprocessed_records(batch_size)
            stats['extracted'] = len(raw_records)
            
            if not raw_records:
                self.logger.info("No unprocessed records found")
                return stats
            
            # Transform
            transformed_records = []
            failed_ids = []
            
            for record in raw_records:
                try:
                    transformed = await self.transform_record(record)
                    transformed_records.append(transformed)
                    stats['transformed'] += 1
                except Exception as e:
                    self.logger.error(f"Failed to transform record {record.get('id')}: {e}")
                    failed_ids.append(record['id'])
                    stats['errors'] += 1
            
            # Load
            if transformed_records:
                await self.load_to_canonical(transformed_records)
                stats['loaded'] = len(transformed_records)
                
                # Update successful records
                success_ids = [r['id'] for r in raw_records if r['id'] not in failed_ids]
                await self.update_processing_status(success_ids, ProcessingStatus.PROCESSED)
            
            # Update failed records
            if failed_ids:
                await self.update_processing_status(
                    failed_ids, 
                    ProcessingStatus.ERROR,
                    "Transformation failed"
                )
            
            self.logger.info(f"ETL batch completed: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"ETL batch processing failed: {e}")
            raise