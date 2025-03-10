from fastapi import APIRouter, HTTPException
from typing import List
from core.dependencies import DBSessionDep
from operations.appointment_operations import AppointmentOperations
from modules.appointment_schema import AppointmentResponse, AppointmentCreate, AppointmentUpdate
from modules.user.error_response_schema import ErrorResponse
import logging

'''
Endpoints for interactions with appointment table
'''

appointment_router = APIRouter(
    prefix="/api/v1/appointments",
    tags=["appointments"],
)

#POST endpoint to create a new appointment in the database
@appointment_router.post("", response_model=AppointmentResponse, responses = {
    500: {"model": ErrorResponse}
})
async def create_appointment(appointment: AppointmentCreate, db_session: DBSessionDep):

    appointment_ops = AppointmentOperations(db_session)
    created_appointment = await appointment_ops.create_appointment(appointment)
    if not created_appointment:
        raise HTTPException(status_code=500, detail="Appointment creation failed")
    return created_appointment

#Get endpoint to get all appointments from the database
@appointment_router.get("", response_model=List[AppointmentResponse], responses = {
    500: {"model": ErrorResponse}
})
async def get_appointments(db_session: DBSessionDep):
    appointment_ops = AppointmentOperations(db_session)
    return await appointment_ops.get_all_appointments()

# GET endpoint to retrieve a specific appointment from the database by the appointment_id
@appointment_router.get("/{appointment_id}", response_model=AppointmentResponse, responses = {
    404: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def get_appointment(appointment_id: int, db_session: DBSessionDep):
    appointment_ops = AppointmentOperations(db_session)
    appointment = await appointment_ops.get_appointment_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment with ID provided not found")
    return appointment

# PUT endpoint to update a specific appointment in the database by the appointment_id
@appointment_router.put("/{appointment_id}", response_model=AppointmentResponse, responses = {
    404: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def update_appointment(appointment_id: int, appointment: AppointmentUpdate, db_session: DBSessionDep):
    appointment_ops = AppointmentOperations(db_session)
    updated_appointment = await appointment_ops.update_appointment(appointment_id, appointment)
    if not updated_appointment:
        raise HTTPException(status_code=404, detail="Appointment with ID provided not found")
    return updated_appointment

# DELETE endpoint to delete an appointment from the database by the appointment_id
@appointment_router.delete("/{appointment_id}", response_model=dict, responses = {
    404: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def delete_appointment(appointment_id: int, db_session: DBSessionDep):
    appointment_ops = AppointmentOperations(db_session)
    success = await appointment_ops.delete_appointment(appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment with ID provided not found")
    return {"message": "Appointment deleted successfully"}