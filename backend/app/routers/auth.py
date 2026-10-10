from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    PasswordChangeRequest,
    EmailChangeRequest,
    ProfileUpdateRequest,
)
from app.security import hash_password, verify_password, create_access_token
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Validates user details, hashes password with Argon2, and stores the user account.",
)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    # Check for existing email address
    existing_user = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash password using Argon2id
    hashed_pwd = hash_password(user_in.password)

    new_user = User(
        full_name=user_in.full_name.strip(),
        email=user_in.email.lower().strip(),
        password_hash=hashed_pwd,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and obtain JWT access token",
    description="Validates email and password, returning a signed short-lived JWT access token upon success.",
)
def login_user(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = db.query(User).filter(User.email == credentials.email.lower().strip()).first()
    if not user:
        raise auth_error

    if not verify_password(credentials.password, user.password_hash):
        raise auth_error

    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns public profile details of the authenticated user derived from JWT claims.",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.put(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change account password",
    description="Verifies the current password and sets the newly provided password.",
)
def change_password(
    req: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "Password changed successfully."}


@router.put(
    "/change-email",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Change account email address",
    description="Verifies the password and updates the account email address.",
)
def change_email(
    req: EmailChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password confirmation.",
        )

    new_email_clean = req.new_email.lower().strip()
    if new_email_clean != current_user.email:
        existing = db.query(User).filter(User.email == new_email_clean).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists.",
            )
        current_user.email = new_email_clean
        db.commit()
        db.refresh(current_user)

    return current_user


@router.put(
    "/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update profile details",
    description="Updates user full name and avatar URL.",
)
def update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.full_name is not None and req.full_name.strip():
        current_user.full_name = req.full_name.strip()
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url.strip()

    db.commit()
    db.refresh(current_user)
    return current_user
