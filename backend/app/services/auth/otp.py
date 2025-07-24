import secrets
import string
from datetime import timedelta
from typing import Optional
import redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class OTPService:
    """Service for handling OTP generation and verification."""
    
    def __init__(self):
        # Initialize Redis connection
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        self.otp_prefix = "otp:"
        self.otp_ttl = 300  # 5 minutes in seconds
        self.max_attempts = 3
        self.rate_limit_ttl = 3600  # 1 hour for rate limiting
    
    def generate_otp(self) -> str:
        """Generate a secure 6-digit OTP."""
        digits = string.digits
        return ''.join(secrets.choice(digits) for _ in range(6))
    
    def store_otp(self, email: str, otp: str) -> bool:
        """Store OTP in Redis with TTL."""
        try:
            key = f"{self.otp_prefix}{email}"
            # Store OTP with metadata
            data = {
                'otp': otp,
                'attempts': 0
            }
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.hset(key, mapping=data)
            pipe.expire(key, self.otp_ttl)
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Failed to store OTP: {str(e)}")
            return False
    
    def verify_otp(self, email: str, otp: str) -> bool:
        """Verify OTP and handle attempts."""
        try:
            key = f"{self.otp_prefix}{email}"
            
            # Check if OTP exists
            if not self.redis_client.exists(key):
                return False
            
            # Get stored data
            stored_data = self.redis_client.hgetall(key)
            stored_otp = stored_data.get('otp')
            attempts = int(stored_data.get('attempts', 0))
            
            # Check if max attempts exceeded
            if attempts >= self.max_attempts:
                self.redis_client.delete(key)
                return False
            
            # Verify OTP
            if stored_otp == otp:
                # Delete OTP on successful verification
                self.redis_client.delete(key)
                return True
            else:
                # Increment attempts
                self.redis_client.hincrby(key, 'attempts', 1)
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify OTP: {str(e)}")
            return False
    
    def is_rate_limited(self, email: str) -> bool:
        """Check if email is rate limited."""
        key = f"rate_limit:{email}"
        count = self.redis_client.get(key)
        return int(count) >= 5 if count else False
    
    def increment_rate_limit(self, email: str) -> None:
        """Increment rate limit counter."""
        key = f"rate_limit:{email}"
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.rate_limit_ttl)
        pipe.execute()
    
    def request_otp(self, email: str) -> Optional[str]:
        """Generate and store OTP with rate limiting."""
        # Check rate limit
        if self.is_rate_limited(email):
            logger.warning(f"Rate limit exceeded for email: {email}")
            return None
        
        # Generate OTP
        otp = self.generate_otp()
        
        # Store OTP
        if self.store_otp(email, otp):
            # Increment rate limit counter
            self.increment_rate_limit(email)
            return otp
        
        return None
    
    def clear_otp(self, email: str) -> None:
        """Clear OTP for an email (useful for testing or admin)."""
        key = f"{self.otp_prefix}{email}"
        self.redis_client.delete(key)


# Singleton instance
otp_service = None

def get_otp_service() -> OTPService:
    """Get or create the OTP service instance."""
    global otp_service
    if otp_service is None:
        otp_service = OTPService()
    return otp_service