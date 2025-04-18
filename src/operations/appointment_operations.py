from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from modules.user.models import (
    Appointment,
    User,
    Barber,
    TimeSlot,
    Appointment_TimeSlot,
    AppointmentService,
    Service,
)
from typing import List, Optional
from fastapi import HTTPException
from modules.appointment_schema import AppointmentCreate, AppointmentResponse
import logging
from operations.email_operations import email_operations

logger = logging.getLogger("appointment_operations")
logger.setLevel(logging.ERROR)

"""
CRUD operations for interacting with the appointment database table
"""


class AppointmentOperations:
    def __init__(self, db: AsyncSession):
        self.db = db

    # create a new appointment
    async def create_appointment(
        self, appointment_data: AppointmentCreate
    ) -> AppointmentResponse:
        try:

            # check if user_id exists in user table
            user_result = await self.db.execute(
                select(User).filter(User.user_id == appointment_data.user_id)
            )
            user = user_result.scalars().first()

            if not user:
                raise HTTPException(
                    status_code=400, detail="Invalid user_id: User does not exist"
                )

            # check if barber_id exists in the Barber table
            barber_result = await self.db.execute(
                select(Barber).filter(Barber.barber_id == appointment_data.barber_id)
            )
            barber = barber_result.scalars().first()

            if not barber:
                raise HTTPException(
                    status_code=400, detail="Invalid barber_id: Barber does not exist"
                )

            # check if slot_id(s) exists in the time_slot table
            appointment_date: str
            for slot_id in appointment_data.time_slot:
                time_slot_result = await self.db.execute(
                    select(TimeSlot).filter(TimeSlot.slot_id == slot_id)
                )
                time_slot = time_slot_result.scalars().first()

                if not time_slot:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid slot_id: Time slot does not exist",
                    )

                appointment_date = time_slot.schedule.date

            # create new appointment if both exist
            new_appointment = Appointment(
                user_id=appointment_data.user_id,
                appointment_date=appointment_date,
                barber_id=appointment_data.barber_id,
                status=appointment_data.status,
            )
            self.db.add(new_appointment)
            await self.db.commit()
            await self.db.refresh(new_appointment)

            # Update the appointment_time_slot table with the newly associated appointment_id and slot_id(s)
            for slot_id in appointment_data.time_slot:
                new_appointment_time_slot = Appointment_TimeSlot(
                    appointment_id=new_appointment.appointment_id, slot_id=slot_id
                )
                self.db.add(new_appointment_time_slot)

            # Update the is_available field in TimeSlot table for the selected slot_id(s)
            await self.db.execute(
                TimeSlot.__table__.update()
                .where(TimeSlot.slot_id.in_(appointment_data.time_slot))
                .values(is_booked=True)
            )

            # Update the service table with the newly associated appointment_id and service_id(s)
            for service_id in appointment_data.service_id:
                new_appointment_service = AppointmentService(
                    service_id=service_id, appointment_id=new_appointment.appointment_id
                )
                self.db.add(new_appointment_service)
            await self.db.commit()

            await self.db.refresh(new_appointment)

            # Refresh appointment again to ensure the session is aware of its latest state
            result = await self.db.execute(
                select(Appointment).filter(
                    Appointment.appointment_id == new_appointment.appointment_id
                ).options(
                    selectinload(Appointment.appointment_time_slots),
                    selectinload(Appointment.appointment_services),
                    selectinload(Appointment.user),
                    selectinload(Appointment.barber),
                )
            )
            appt = result.scalars().first()

            if not appt:
                return None
            
             # Send out booking confirmation emails
            try:
                # Retrieve all necessary information from DB for crafting custom emails based on specific appointment
                booking_user_result = await self.db.execute(select(User).filter(User.user_id == appt.user_id))
                booking_user = booking_user_result.scalars().first()

                barber_result = await self.db.execute(select(Barber).filter(Barber.barber_id == appt.barber_id))
                barber = barber_result.scalars().first()

                barber_information_result = await self.db.execute(select(User).filter(User.user_id == barber.user_id))
                barber_information = barber_information_result.scalars().first()

                service_information_result = await self.db.execute(select(Service).filter(Service.service_id == appointment_data.service_id))
                service_information = service_information_result.scalars().first()
                
                slots = []
                for slot_id in appointment_data.time_slot:
                    time_slot_result = await self.db.execute(select(TimeSlot).filter(TimeSlot.slot_id == slot_id))
                    time_slot = time_slot_result.scalars().first()
                    if time_slot:
                        slots.append(time_slot)

                first_slot = min(slots, key=lambda slot: slot.start_time) if slots else None

                if first_slot:
                    appointment_time = first_slot.start_time.strftime('%I:%M %p')
                    appointment_date = first_slot.schedule.date.strftime('%B %d, %Y')

                # Send email to the client
                await email_operations.send_email(
                    f"{booking_user.email}",
                    "Barber shop appointment scheduled successfully!",
                    f"""
                    {booking_user.firstName},
                    your appointment for a {service_information.name} with {barber_information.firstName} {barber_information.lastName} 
                    was successfully scheduled for {appointment_time} on {appointment_date}.
                    """
                )

                # Send email to the barber
                await email_operations.send_email(
                    f"{barber_information.email}",
                    "A client has scheduled an appointment",
                    f"""
                    {barber_information.firstName},
                    {booking_user.firstName} {booking_user.lastName} has scheduled a {service_information.name} with
                    you at {appointment_time} on {appointment_date}.        
                    """
                )
            
            # Log if there is an issue sending confirmation emails, but appointment will still be created
            except Exception as e:
                logger.error(f"An error occurred while sending confirmation emails: {e}")


            return appt.to_response_schema()

        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred during appointment creation",
            )

    # Get all appointments
    async def get_all_appointments(
        self,
        page: int,
        limit: int,
        user_id: Optional[int] = None,
        barber_id: Optional[int] = None,
    ) -> List[AppointmentResponse]:
        try:
            # Calculate offset for SQL query
            offset = (page - 1) * limit

            result = await self.db.execute(
                select(Appointment).limit(limit).offset(offset)
            )
            appointments = result.scalars().all()

            if not appointments:
                return None
            return [app.to_response_schema() for app in appointments]

        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while fetching appointments",
            )

    # Get a specific appointment by its id
    async def get_appointment_by_id(
        self, appointment_id: int
    ) -> Optional[AppointmentResponse]:
        # try:
        result = await self.db.execute(
            select(Appointment).filter(Appointment.appointment_id == appointment_id)
        )
        appt = result.scalars().first()

        if not appt:
            return None

        return appt.to_response_schema()

        # except SQLAlchemyError:
        #     raise HTTPException(
        #         status_code=500,
        #         detail="An unexpected error occurred while fetching the appointment"
        #     )

    # Update an existing appointment
    async def update_appointment(
        self, appointment_id: int, appointment_data
    ) -> Optional[AppointmentResponse]:
        try:
            result = await self.db.execute(
                select(Appointment).filter(Appointment.appointment_id == appointment_id)
            )
            appointment = result.scalars().first()

            if not appointment:
                return None

            # Update the appointment's info
            update_data = appointment_data.dict(
                exclude_unset=True, exclude={"time_slot", "service_id"}
            )
            for key, value in update_data.items():
                setattr(appointment, key, value)

            # update Appointment_TimeSlot table if it has new tim_slot info
            if "time_slot" in appointment_data.dict(exclude_unset=True):
                # Delete current associations for this appointment
                await self.db.execute(
                    delete(Appointment_TimeSlot).where(
                        Appointment_TimeSlot.appointment_id == appointment_id
                    )
                )
                # Add new associations
                for slot_id in appointment_data.time_slot:
                    new_link = Appointment_TimeSlot(
                        appointment_id=appointment_id, slot_id=slot_id
                    )
                    self.db.add(new_link)

            # update AppointmentService table if it has new service_id information
            if "service_id" in appointment_data.dict(exclude_unset=True):
                await self.db.execute(
                    delete(AppointmentService).where(
                        AppointmentService.appointment_id == appointment_id
                    )
                )
                for svc_id in appointment_data.service_id:
                    new_service_link = AppointmentService(
                        appointment_id=appointment_id, service_id=svc_id
                    )
                    self.db.add(new_service_link)

            # Commit all changes
            await self.db.commit()
            await self.db.refresh(appointment)

            # Retrieve the updated data for the response
            time_slot_result = await self.db.execute(
                select(Appointment_TimeSlot).where(
                    Appointment_TimeSlot.appointment_id == appointment_id
                )
            )
            time_slot_links = time_slot_result.scalars().all()
            time_slot_ids = [link.slot_id for link in time_slot_links]

            service_result = await self.db.execute(
                select(AppointmentService).where(
                    AppointmentService.appointment_id == appointment_id
                )
            )
            service_links = service_result.scalars().all()
            service_ids = [link.service_id for link in service_links]

            # Return with updated data
            return AppointmentResponse(
                appointment_id=appointment.appointment_id,
                user_id=appointment.user_id,
                barber_id=appointment.barber_id,
                status=appointment.status,
                time_slot=time_slot_ids,
                service_id=service_ids,
            )

        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while updating the desired appointment",
            )

    # Delete an appointment
    async def delete_appointment(self, appointment_id: int) -> bool:
        try:
            result = await self.db.execute(
                select(Appointment).filter(Appointment.appointment_id == appointment_id)
            )
            appointment = result.scalars().first()

            if not appointment:
                return False

            # Delete associated appointment_time_slot records
            await self.db.execute(
                delete(Appointment_TimeSlot).where(
                    Appointment_TimeSlot.appointment_id == appointment_id
                )
            )
            # Delete associated appointment_service records
            await self.db.execute(
                delete(AppointmentService).where(
                    AppointmentService.appointment_id == appointment_id
                )
            )

            await self.db.delete(appointment)
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while deleting the desired appointment",
            )
