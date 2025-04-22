from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from core.dependencies import DBSessionDep
from operations.user_operations import UserOperations
from modules.user.user_schema import UserResponse, UserCreate, UserUpdate, UserPasswordUpdate
from auth.controller import AuthController
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from modules.user.error_response_schema import ErrorResponse


'''
Endpoints for interactions with users table
'''

user_router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)
# Initialize the HTTPBearer scheme for authentication
bearer_scheme = HTTPBearer()

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
async def get_users(
    db_session: DBSessionDep, 
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100)
):
    AuthController.protected_endpoint(credentials, required_role="barber")
    
    user_ops = UserOperations(db_session)
    return await user_ops.get_all_users(page, limit)

@user_router.get("/me", response_model=UserResponse, responses = {
    400: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def get_current_user(db_session: DBSessionDep, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    # Get the current user from the token
    user_info = AuthController.protected_endpoint(credentials)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user_ops = UserOperations(db_session)
    user = await user_ops.get_user_by_kc_id(user_info.id)
    
    return user.to_response_schema()

# GET endpoint to retrieve a specific user in the database by their ID
@user_router.get("/{user_id}", response_model=UserResponse, responses= {
     400: {"model": ErrorResponse},
     500: {"model": ErrorResponse}
})
async def get_user(user_id: int, db_session: DBSessionDep, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    AuthController.protected_endpoint(credentials)
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
async def update_user(user_id: int, user: UserUpdate, db_session: DBSessionDep, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    AuthController.protected_endpoint(credentials)
    user_ops = UserOperations(db_session)
    updated_user = await user_ops.update_user(user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found with ID provided")
    
    return updated_user

# POST endpoint to update a user's password
@user_router.post("/{user_id}/update-password", responses={
    400: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
}, operation_id="updateUserPassword")
async def update_user_password(
    user_id: int,
    password_data: UserPasswordUpdate,
    db_session: DBSessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    AuthController.protected_endpoint(credentials)
    user_ops = UserOperations(db_session)
    success = await user_ops.update_user_password(user_id, password_data)
    if not success:
        raise HTTPException(status_code=404, detail="User not found with ID provided")
    
    return {"message": "Password updated successfully"}

# DELETE endpoint to delete a user from the database by their ID
@user_router.delete("/{user_id}", response_model=dict, responses = {
    404: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def delete_user(user_id: int, db_session: DBSessionDep, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    AuthController.protected_endpoint(credentials, required_role="admin")
    user_ops = UserOperations(db_session)
    success = await user_ops.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found with ID provided")
    return {"message": "User deleted successfully"}

