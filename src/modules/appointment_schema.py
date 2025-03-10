from pydantic import BaseModel
from typing import Optional
from enum import Enum

'''
Pydantic validation models for the appointment table endpoints
'''

class AppointmentStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"

class AppointmentCreate(BaseModel):
    user_id: int
    barber_id: int
    status: AppointmentStatus 

class AppointmentUpdate(BaseModel):
    user_id: Optional[int] = None
    barber_id: Optional[int] = None
    status: Optional[AppointmentStatus] = None

class AppointmentResponse(AppointmentCreate):
    appointment_id: int

    class Config:
        from_attributes = True