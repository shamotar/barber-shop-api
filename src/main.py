from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from core.db import sessionmanager
from routers.user_router import user_router
from auth.models import TokenResponse, UserInfo
from auth.controller import AuthController
from routers.barber_router import barber_router
from routers.service_router import service_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)

# Initialize the HTTPBearer scheme for authentication
bearer_scheme = HTTPBearer()

# Middleware configuration for Frontend-Backend communication
app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        # Only localhost for now
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Connect user_router
app.include_router(user_router)

# Connect barber_router
app.include_router(barber_router)

# Connect service_router
app.include_router(service_router)


# Define the root endpoint
@app.get("/")
async def read_root():
    """
    Root endpoint that provides a welcome message and documentation link.
    """
    return AuthController.read_root()

# Define the login endpoint
@app.post("/login", response_model=TokenResponse)
async def login(username: str = Form(...), password: str = Form(...)):
    """
    Login endpoint to authenticate the user and return an access token.

    Args:
        username (str): The username of the user attempting to log in.
        password (str): The password of the user.

    Returns:
        TokenResponse: Contains the access token upon successful authentication.
    """
    return AuthController.login(username, password)

# Define the protected endpoint
@app.get("/protected", response_model=UserInfo)
async def protected_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Protected endpoint that requires a valid token for access.

    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token provided via HTTP Authorization header.

    Returns:
        UserInfo: Information about the authenticated user.
    """
    return AuthController.protected_endpoint(credentials)


# Protected role-based endpoint for testing
@app.get("/barber/protected", response_model=UserInfo)
async def barber_protected(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    return AuthController.protected_endpoint(credentials, required_role="barber")


@app.get("/healthz")
async def root():
    return {"healthy": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)