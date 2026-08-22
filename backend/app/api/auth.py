"""Per-user accounts: register, login, logout, current-user.

This is additive to the shared API_ACCESS_TOKEN in security.py, not a
replacement — see db/user_models.py for why. This router is gated by the
same `require_access` dependency as every other one: the shared token is
still what keeps the deployed instance private to the team, and a personal
login is a second, identity layer on top of that gate, for the specific
actions (audit entries) that need a real "who did this" rather than the
whole API needing to know who is calling.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..services import auth_service as auth

router = APIRouter(prefix="/api/auth", tags=["Accounts"])

SESSION_HEADER = "X-Session-Token"


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=254)
    name: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., max_length=200)


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str


class LoginResponse(BaseModel):
    user: UserOut
    session_token: str


def get_current_user(request: Request) -> auth.AuthenticatedUser:
    """FastAPI dependency: the logged-in user, or 401.

    Use on the specific actions that need a real identity (audit entries),
    not globally — most of the API remains gated only by the shared token.
    """
    token = request.headers.get(SESSION_HEADER)
    user = auth.resolve_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Log in to perform this action.")
    return user


@router.post("/register", response_model=UserOut)
async def register(request: RegisterRequest):
    try:
        user = auth.register_user(request.email, request.name, request.password)
    except auth.AuthError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return UserOut(id=user.id, email=user.email, name=user.name, role=user.role)


@router.post("/login", response_model=LoginResponse)
async def login_route(request: LoginRequest):
    try:
        user, token = auth.login(request.email, request.password)
    except auth.AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return LoginResponse(
        user=UserOut(id=user.id, email=user.email, name=user.name, role=user.role),
        session_token=token,
    )


@router.post("/logout")
async def logout_route(request: Request):
    token = request.headers.get(SESSION_HEADER)
    if token:
        auth.logout(token)
    return {"logged_out": True}


@router.get("/me", response_model=UserOut)
async def me(request: Request):
    user = get_current_user(request)
    return UserOut(id=user.id, email=user.email, name=user.name, role=user.role)
