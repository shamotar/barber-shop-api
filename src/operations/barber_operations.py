from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from modules.user.models import Barber, Schedule, User
from modules.user.barber_schema import BarberCreate

from auth.service import AuthService
import logging

logger = logging.getLogger("barber_operations")
logger.setLevel(logging.ERROR)
'''
Contains methods for barber creation and retrieval.
Updating a Barber's information should be done using the User ID in the user router.
Barbers should be deleted from the system using the user router as well.
'''
class BarberOperations:

    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Create a Barber
    async def create_barber(self, user: BarberCreate) -> Barber:
        try:
            result = await self.db.execute(select(User).filter(User.user_id == user.user_id))
            user_object = result.scalars().first()

            # Check to make sure the User ID provided links to a valid User
            if not user_object:
                raise HTTPException(
                    status_code = 400,
                    detail="User not found with provided ID"
                )
            
            existing_barber = await self.db.execute(select(Barber).filter(Barber.user_id == user.user_id))
            first_existing_barber = existing_barber.scalars().first()

            # Make sure the user is not already a barber
            if first_existing_barber:
                raise HTTPException(
                    status_code=400,
                    detail="User is already a barber"
                )
        
        
            barber = Barber(user_id=user.user_id)
            self.db.add(barber)
            await self.db.commit()
            await self.db.refresh(barber)

            # Add barber role to Keycloak user
            try:
                AuthService.add_role_to_user(user_object.kc_id, "barber")
            except Exception as e:
                logger.error(f"Error adding role to Keycloak user: {str(e)}")
                await self.db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Error adding role to Keycloak user: {str(e)}"
                )

            return barber

        except SQLAlchemyError as e:
            logger.error(e)
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
    
    # Retrieve all barbers
    async def get_all_barbers(self, page: int, limit: int) -> List[Barber]:
        try: 
            # Calculate offset for SQL query
            offset = (page - 1) * limit

            result = await self.db.execute(select(Barber).limit(limit).offset(offset))
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
        
    # Retrieve a specific barber by their Barber ID
    async def get_barber_by_id(self, barber_id: int):
        try:
            result = await self.db.execute(select(Barber).filter(Barber.barber_id == barber_id))
            first_result = result.scalars().first()
            if not first_result:
                raise HTTPException(status_code = 400, detail="No barber found with provided ID")
            else:
                return first_result
        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
        
    # Retrieve a specific barber by their User ID
    async def get_barber_by_user_id(self, user_id: int):
        try:
            result = await self.db.execute(select(Barber).filter(Barber.user_id == user_id))
            first_result = result.scalars().first()
            if not first_result:
                raise HTTPException(status_code = 400, detail="No barber found with provided User ID")
            else:
                return first_result
        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
        
    async def list_barbers_by_schedule_date(self, schedule_date: str, page: int = None, limit: int = None) -> List[Barber]:
        # Get a Schedule object by date
        schedules = await self.db.execute(select(Schedule).filter(Schedule.date == schedule_date))
        schedules = schedules.scalars().all()
        if not schedules:
            return []

        # Get all barbers by joining the Schedule table on the barber_id
        result = await self.db.execute(
            select(Barber).join(Schedule).filter(Schedule.schedule_id.in_([schedule.schedule_id for schedule in schedules])
            ).distinct(Barber.barber_id)
        )
        barbers = result.scalars().all()
        if page and limit:
            offset = (page - 1) * limit
            barbers = barbers[offset:offset + limit]
        return barbers

