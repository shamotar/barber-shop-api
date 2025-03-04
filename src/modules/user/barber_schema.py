from pydantic import BaseModel
from typing import Optional

class BarberBase(BaseModel):
    user_id: int

class BarberResponse(BarberBase):
    barber_id: int

    class Config:
        from_attributes = True