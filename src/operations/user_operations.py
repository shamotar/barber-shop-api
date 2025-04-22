from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from modules.user.models import User
from modules.user.user_schema import UserCreate, UserUpdate, UserPasswordUpdate
from typing import List, Optional
from fastapi import HTTPException

from auth.service import AuthService
import logging

logger = logging.getLogger("user_operations")
logger.setLevel(logging.ERROR)

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
            try:
                kc_id = AuthService.register_kc_user(new_user)
                if not kc_id:
                    raise HTTPException(status_code=400, detail="Keycloak user creation has failed")
                new_user.kc_id = kc_id
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error creating Keycloak user: {str(e)}"
                )
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            
            return new_user
        # If another error is returned that was somehow not caught above, return generic error message.
        except SQLAlchemyError as e:
            logger.error(e)
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred: {str(e)}"
            )

    # Get all users
    async def get_all_users(self, page: int, limit: int) -> List[User]:
        try:

            # Calculate offset based on page/limit provided by client
            offset = (page - 1) * limit

            result = await self.db.execute(select(User).limit(limit).offset(offset))
            return result.scalars().all()
        # Not anticipating many errors here, but just in case
        except SQLAlchemyError as e:
            logger.error(e)
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
        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occured"
            )
        
    async def get_user_by_kc_id(self, kc_id: str) -> User:
        try:
            result = await self.db.execute(select(User).filter(User.kc_id == kc_id))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found with ID provided")
            return user
        # Handle generic exceptions, wrong ID provided error already handled in router
        except SQLAlchemyError as e:
            logger.error(e)
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occured"
            )

    # Update user by their ID
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        try:
            if user_data.email:
                existing_user_email = await self.db.execute(select(User).filter(User.email == user_data.email, User.user_id != user_id))
                # Check if the email already exists for another user
                if existing_user_email.scalars().first():
                    raise HTTPException(status_code=400, detail="A user already exists with the provided email")

            if user_data.phoneNumber:
                existing_user_phone = await self.db.execute(select(User).filter(User.phoneNumber == user_data.phoneNumber, User.user_id != user_id))
                # Check if the phone number already exists for another user
                if existing_user_phone.scalars().first():
                    raise HTTPException(status_code=400, detail="A user already exists with the provided phone number")

                if len(user_data.phoneNumber) > 10:
                    raise HTTPException(status_code=400, detail="Phone number must be 10 digits or less")

        
            result = await self.db.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            if not user:
                return None

            for key, value in user_data.model_dump(exclude_unset=True).items():
                setattr(user, key, value)

            # Update Keycloak user data# Update user in Keycloak
            try:
                AuthService.update_kc_user(user)
            except Exception as e:
                logger.error(e)
                # Rollback database changes if Keycloak update fails
                await self.db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Error updating Keycloak user: {str(e)}"
                )
            
            # Update database user data
            await self.db.commit()
            await self.db.refresh(user)

            return user
    
        except SQLAlchemyError as e:
            logger.error(e)
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
        except SQLAlchemyError as e:
            logger.error(e)
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occured"
            )
        
    # Update user password
    async def update_user_password(self, user_id: int, password_data: UserPasswordUpdate) -> bool:
        try:
            # Get user from database
            result = await self.db.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            if not user:
                return False
            
            # Check if the old password is correct
            try:
                AuthService.authenticate_user(user.email, password_data.old_password)
            except Exception as e:
                logger.error(e)
                raise HTTPException(status_code=400, detail="Old password is incorrect")

            # Check if new password and confirm password match
            if password_data.new_password != password_data.confirm_password:
                raise HTTPException(status_code=400, detail="New password and confirm password do not match")

            # Update the user's password in Keycloak
            try:
                AuthService.update_kc_user_password(user.kc_id, password_data.new_password)
            except Exception as e:
                logger.error(e)
                # Rollback database changes if Keycloak update fails
                await self.db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Error updating Keycloak user password: {str(e)}"
                )

            return True
        
        # Handle generic exceptions, wrong ID provided error already handled in router
        except SQLAlchemyError as e:
            logger.error(e)
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occured"
            )