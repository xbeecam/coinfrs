from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth, OAuthError
from httpx import AsyncClient
from fastapi import HTTPException, status
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """Service for handling Google OAuth authentication."""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Google OAuth credentials not configured")
        
        # Initialize OAuth client
        self.oauth = OAuth()
        self.oauth.register(
            name='google',
            client_id=self.client_id,
            client_secret=self.client_secret,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
    
    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate the Google OAuth authorization URL."""
        client = self.oauth.create_client('google')
        return client.create_authorization_url(redirect_uri, state=state)['url']
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        try:
            client = self.oauth.create_client('google')
            token = await client.fetch_token(
                code=code,
                redirect_uri=redirect_uri,
                grant_type='authorization_code'
            )
            return token
        except OAuthError as e:
            logger.error(f"OAuth token exchange failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )
    
    async def get_user_info(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch user information from Google using the access token."""
        try:
            async with AsyncClient() as client:
                headers = {'Authorization': f"Bearer {token['access_token']}"}
                response = await client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch user info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user information from Google"
            )
    
    async def authenticate_user(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Complete OAuth flow: exchange code for token and fetch user info."""
        # Exchange code for token
        token = await self.exchange_code_for_token(code, redirect_uri)
        
        # Fetch user info
        user_info = await self.get_user_info(token)
        
        # Extract relevant fields
        return {
            'google_auth_id': user_info.get('id'),
            'email': user_info.get('email'),
            'email_verified': user_info.get('verified_email', False),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'raw_data': user_info  # Store full response for reference
        }


# Singleton instance
google_oauth_service = None

def get_google_oauth_service() -> GoogleOAuthService:
    """Get or create the Google OAuth service instance."""
    global google_oauth_service
    if google_oauth_service is None:
        google_oauth_service = GoogleOAuthService()
    return google_oauth_service