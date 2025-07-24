from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.user import UserCreate, UserResponse, GoogleAuthCallback, OTPRequest, OTPVerify
from app.schemas.token import Token
from app.crud.user import get_user_by_email, create_user, get_user_by_google_id, create_oauth_user
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.services.auth.google import get_google_oauth_service
from app.services.auth.otp import get_otp_service
from app.services.auth.email import get_email_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=UserResponse, deprecated=True, description="Deprecated: Use Google OAuth or Email OTP instead")
def register_user(
    *,
    session: Session = Depends(get_session),
    user_in: UserCreate,
):
    """
    Create new user.
    """
    user = get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=409,
            detail="The user with this email already exists in the system.",
        )
    user = create_user(session=session, user_in=user_in)
    return user

@router.post("/login", response_model=Token, deprecated=True, description="Deprecated: Use Google OAuth or Email OTP instead")
def login(
    response: Response,
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = get_user_by_email(session=session, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/oauth/google")
def google_oauth_redirect(
    redirect_uri: str = Query(
        default=f"{settings.BACKEND_CORS_ORIGINS[0]}/auth/google/callback",
        description="URI to redirect after Google authentication"
    )
):
    """
    Redirect to Google OAuth for authentication.
    """
    try:
        oauth_service = get_google_oauth_service()
        auth_url = oauth_service.get_authorization_url(redirect_uri)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )

@router.post("/oauth/google/callback", response_model=Token)
async def google_oauth_callback(
    response: Response,
    callback_data: GoogleAuthCallback,
    session: Session = Depends(get_session),
):
    """
    Handle Google OAuth callback and create/login user.
    """
    try:
        oauth_service = get_google_oauth_service()
        
        # Complete OAuth flow
        redirect_uri = f"{settings.BACKEND_CORS_ORIGINS[0]}/auth/google/callback"
        user_data = await oauth_service.authenticate_user(
            code=callback_data.code,
            redirect_uri=redirect_uri
        )
        
        # Check if user exists by Google ID
        user = get_user_by_google_id(
            session=session, 
            google_id=user_data['google_auth_id']
        )
        
        if not user:
            # Check if user exists by email
            user = get_user_by_email(session=session, email=user_data['email'])
            
            if user:
                # Link existing user to Google account
                user.google_auth_id = user_data['google_auth_id']
                session.add(user)
                session.commit()
            else:
                # Create new OAuth user
                user = create_oauth_user(
                    session=session,
                    email=user_data['email'],
                    google_auth_id=user_data['google_auth_id']
                )
        
        # Generate tokens
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        # Set refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict"
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.post("/otp/request")
async def request_otp(
    otp_request: OTPRequest,
    session: Session = Depends(get_session),
):
    """
    Request OTP for passwordless login. OTP will be sent to the provided email.
    """
    # Check if user exists
    user = get_user_by_email(session=session, email=otp_request.email)
    
    # Always return success for security (don't reveal if email exists)
    # But only send OTP if user exists
    if user:
        otp_service = get_otp_service()
        otp = otp_service.request_otp(otp_request.email)
        
        if otp:
            # Send OTP via email
            email_service = get_email_service()
            email_sent = email_service.send_otp_email(otp_request.email, otp)
            
            if not email_sent:
                logger.error(f"Failed to send OTP email to {otp_request.email}")
        else:
            # Rate limited
            logger.warning(f"OTP request rate limited for {otp_request.email}")
    
    return {"message": "If the email exists, an OTP has been sent."}

@router.post("/otp/verify", response_model=Token)
async def verify_otp(
    response: Response,
    otp_verify: OTPVerify,
    session: Session = Depends(get_session),
):
    """
    Verify OTP and login user.
    """
    # Get user
    user = get_user_by_email(session=session, email=otp_verify.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or OTP"
        )
    
    # Verify OTP
    otp_service = get_otp_service()
    is_valid = otp_service.verify_otp(otp_verify.email, otp_verify.otp)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or OTP"
        )
    
    # If user doesn't exist yet (shouldn't happen with current flow), create user
    if not user:
        user = create_user(
            session=session,
            user_in=UserCreate(email=otp_verify.email, password=None)
        )
        
        # Send welcome email
        email_service = get_email_service()
        email_service.send_welcome_email(user.email)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
