from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from core.db import async_session_manager
from core.config import settings
from routers.user_router import user_router
from auth.controller import AuthController
from routers.barber_router import barber_router
from routers.service_router import service_router
from routers.schedule_router import schedule_router
from routers.auth_router import auth_router
from routers.appointment_router import appointment_router
from routers.thread_router import thread_router
from routers.message_router import message_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if async_session_manager._engine is not None:
        # Close the DB connection
        await async_session_manager.close()


app = FastAPI(lifespan=lifespan)

# Initialize the HTTPBearer scheme for authentication
bearer_scheme = HTTPBearer()

# Middleware configuration for Frontend-Backend communication
app.add_middleware(
    CORSMiddleware,

    allow_origins=settings.get_config()["backend_cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Connect routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(barber_router)
app.include_router(service_router)
app.include_router(schedule_router)
app.include_router(appointment_router)
app.include_router(thread_router)
app.include_router(message_router)

# Define the root endpoint
@app.get("/")
async def root():
    return {"Barbershop App"}

@app.get("/healthz")
async def root():
    return {"healthy": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)