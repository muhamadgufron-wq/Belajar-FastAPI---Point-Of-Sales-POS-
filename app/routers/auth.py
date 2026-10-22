from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Daftar akun baru",
)
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    """Mendaftar user baru dengan password yang di-hash (Argon2id)."""
    existing_user = session.exec(
        select(User).where(User.username == user_in.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username sudah terdaftar, silakan gunakan username lain.",
        )

    hashed_pwd = hash_password(user_in.password)

    new_user = User(
        username=user_in.username,
        password=hashed_pwd,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="Login dan dapatkan JWT Token",
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session),
):
    """Login menggunakan username & password untuk memperoleh Bearer JWT Token."""
    user = session.exec(
        select(User).where(User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Akun ini sedang dinonaktifkan",
        )

    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserRead,
    summary="Profil user yang sedang login",
)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Mengambil data profil user saat ini dari JWT token."""
    return current_user
