from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from core.db import get_db_session
from core.dependencies import DBSessionDep
from operations.user_operations import UserOperations
from modules.user.user_schema import UserResponse, UserCreate, UserBase, UserUpdate
from auth.service import AuthService
import logging
from modules.user.error_response_schema import ErrorResponse
'''
Endpoints for interactions with users table
'''

user_router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)

# POST endpoint to create a new user in the database
@user_router.post("", response_model=UserResponse, responses = {
    400: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def create_user(user: UserCreate, db_session: DBSessionDep):

    # Creates a user in DB
    user_ops = UserOperations(db_session)
    created_user = await user_ops.create_user(user)
    if not created_user:
        raise HTTPException(status_code=400, detail="User creation failed")
    
    return created_user

# GET endpoint to get all users from the database
@user_router.get("", response_model=List[UserResponse], responses = {
    500: {"model": ErrorResponse}
})
async def get_users(db_session: DBSessionDep):
    user_ops = UserOperations(db_session)
    return await user_ops.get_all_users()

# GET endpoint to retrieve a specific user in the database by their ID
@user_router.get("/{user_id}", response_model=UserResponse, responses= {
     400: {"model": ErrorResponse},
     500: {"model": ErrorResponse}
})
async def get_user(user_id: int, db_session: DBSessionDep):
    user_ops = UserOperations(db_session)
    user = await user_ops.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found with ID provided")
    return user

# PUT endpoint to update a specific user in the database by their ID
@user_router.put("/{user_id}", response_model=UserResponse, responses = {
    400: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def update_user(user_id: int, user: UserUpdate, db_session: DBSessionDep):
    user_ops = UserOperations(db_session)
    updated_user = await user_ops.update_user(user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found with ID provided")
    return updated_user

# DELETE endpoint to delete a user from the database by their ID
@user_router.delete("/{user_id}", response_model=dict, responses = {
    404: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def delete_user(user_id: int, db_session: DBSessionDep):
    user_ops = UserOperations(db_session)
    success = await user_ops.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found with ID provided")
    return {"message": "User deleted successfully"}

