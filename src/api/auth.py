import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.database.database import get_db
from src.schemas import RequestEmail, Token, User, UserCreate
from src.services.auth import Hash, create_access_token, get_email_from_token
from src.services.email import send_email
from src.services.users import UserService

logger = logging.getLogger("rate_limiter")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Received registration request: %s", user.dict())
    service = UserService(db)
    print("Received request:", user)
    try:
        existing_user_by_email = await service.get_user_by_email(user.email)
        if existing_user_by_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        existing_user_by_username = await service.get_user_by_username(user.username)
        if existing_user_by_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this username already exists",
            )

        user.password = Hash().get_password_hash(user.password)
        logger.info("Password hashed successfully")

        new_user = await service.create_user(user)
        logger.info("User created successfully: %s", new_user.email)

        background_tasks.add_task(
            send_email, new_user.email, new_user.username, request.base_url
        )
        return new_user
    except Exception as e:
        logger.error("Error in register_user: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    service = UserService(db)
    db_user = await service.get_user_by_username(form_data.username)

    if not db_user or not Hash().verify_password(
        form_data.password, db_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified",
        )

    access_token = await create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    email = await get_email_from_token(token)
    service = UserService(db)
    user = await service.get_user_by_email(email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification error",
        )

    if user.is_verified:
        return {"message": "Your email is already verified"}

    await service.confirm_email(email)
    return {"message": "Email verified successfully"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    user = await service.get_user_by_email(body.email)

    if user and user.is_verified:
        return {"message": "Your email is already verified"}

    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )

    return {"message": "Check your email for verification"}
