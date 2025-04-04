from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from modules.user.models import User
from pydantic import EmailStr
from modules.user.user_schema import UserCreate, UserBase
from typing import List, Optional
from fastapi import HTTPException
from auth.service import AuthService
'''
CRUD operations for interacting with users database table
'''
class UserOperations:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Create a user
    async def create_user(self, user_data: UserCreate) -> User:
        
        '''
        Checking for three most common errors:
        A phone number or email already exists, or phone number is greater than 10 digits
        '''
        existing_user_email = await self.db.execute(select(User).filter(User.email == user_data.email))

        if existing_user_email.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="A user already exists with the provided email"
            )
        
        existing_user_phone = await self.db.execute(select(User).filter(User.phoneNumber == user_data.phoneNumber))

        if existing_user_phone.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="A user already exists with the provided phone number"
            )
        
        if len(user_data.phoneNumber) > 10:
            raise HTTPException(
                status_code=400,
                detail="Phone number must be 10 digits or less"
            )

        try:
            # Creates a new user
            new_user = User(**user_data.model_dump())

            # Add new user to Keycloak  
            created_kc_user = AuthService.register_kc_user(new_user)
            print("********TestUSER",new_user)
            if not created_kc_user:
                raise HTTPException(status_code=400, detail=f"Keycloak user creation has failed")
            
            # Add new user to DB
            new_user.kc_id = created_kc_user
            print("********TestUSERKCID",new_user)
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            
            return new_user
        # If another error is returned that was somehow not caught above, return generic error message.
        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occured"
            )

    # Get all users
    async def get_all_users(self, page: int, limit: int) -> List[User]:
        try:

            # Calculate offset based on page/limit provided by client
            offset = (page - 1) * limit

            result = await self.db.execute(select(User).limit(limit).offset(offset))
            return result.scalars().all()
        # Not anticipating many errors here, but just in case
        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occured"
            )


    # Get a specific user by their ID
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        try:
            result = await self.db.execute(select(User).filter(User.user_id == user_id))
            return result.scalars().first()
        # Handle generic exceptions, wrong ID provided error already handled in router
        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occured"
            )

    # Update user by their ID
    async def update_user(self, user_id: int, user_data) -> Optional[User]:
        if user_data.email:
            existing_user_email = await self.db.execute(select(User).filter(User.email == user_data.email))
            if existing_user_email.scalars().first():
                raise HTTPException(status_code=400, detail="A user already exists with the provided email")

        if user_data.phoneNumber:
            existing_user_phone = await self.db.execute(select(User).filter(User.phoneNumber == user_data.phoneNumber))
            if existing_user_phone.scalars().first():
                raise HTTPException(status_code=400, detail="A user already exists with the provided phone number")

            if len(user_data.phoneNumber) > 10:
                raise HTTPException(status_code=400, detail="Phone number must be 10 digits or less")

        try:
            result = await self.db.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            if not user:
                return None

            for key, value in user_data.dict(exclude_unset=True).items():
                setattr(user, key, value)

            # Update Keycloak user data
            AuthService.update_kc_user(user_data)

            # Update database user data
            await self.db.commit()
            await self.db.refresh(user)
            return user
    
        except SQLAlchemyError:
            raise HTTPException(
                status_code=500, 
                detail="An unexpected error occurred"
                )


    # Delete a user by their ID
    async def delete_user(self, user_id: int) -> bool:
        try:
            # Get user from database
            result = await self.db.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            if not user:
                return False
            
            # Delete user from Keycloak server
            AuthService.delete_kc_user(user.email)

            # Delete user from database
            await self.db.delete(user)
            await self.db.commit()
            return True
        
        # Handle generic exceptions, wrong ID provided error already handled in router
        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occured"
            )