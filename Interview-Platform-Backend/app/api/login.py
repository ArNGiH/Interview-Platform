from fastapi import APIRouter
from fastapi import Depends

from app.core.auth import get_current_user
from app.core.auth import CurrentUser

router = APIRouter(
    prefix="/user",
    tags=["User"]
)


@router.get("/info")
def get_user_info(
    current_user: CurrentUser = Depends(get_current_user)
):

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "picture_url": current_user.picture_url,
        "is_authenticated": True
    }
