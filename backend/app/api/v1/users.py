from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.canonical import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user.
    """
    return current_user
