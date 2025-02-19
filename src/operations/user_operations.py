from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from modules.user.models import User
from pydantic import EmailStr
from modules.user.user_schema import UserCreate, UserBase
from typing import List, Optional
from fastapi import HTTPException

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
            new_user = User(**user_data.model_dump())
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user
        # If another error is returned that was somehow not caught above, return generic error message.
        except SQLAlchemyError:
            raise HTTPException(
                status_code=400,
                detail=f"An unexpected error occured"
            )

    # Get all users
    async def get_all_users(self) -> List[User]:
        try:
            result = await self.db.execute(select(User))
            return result.scalars().all()
        # Not anticipating many errors here, but just in case
        except SQLAlchemyError:
            raise HTTPException(
                status_code=400,
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
                status_code=400,
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

            await self.db.commit()
            await self.db.refresh(user)
            return user
    
        except SQLAlchemyError:
            raise HTTPException(
                status_code=400, 
                detail="An unexpected error occurred"
                )


    # Delete a user by their ID
    async def delete_user(self, user_id: int) -> bool:
        try:
            result = await self.db.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            if not user:
                return False
            await self.db.delete(user)
            await self.db.commit()
            return True
        # Handle generic exceptions, wrong ID provided error already handled in router
        except SQLAlchemyError:
            raise HTTPException(
                status_code=400,
                detail="An unexpected error occured"
            )