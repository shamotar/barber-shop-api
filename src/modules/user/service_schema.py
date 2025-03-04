from datetime import time
from decimal import Decimal
from typing import Annotated, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Float


class ServiceBase(BaseModel):
    name: str
    duration: time
    price: Annotated[Decimal, Field(ge=0, max_digits=5, decimal_places=2)]

class ServiceResponse(ServiceBase):
    service_id: int

    class Config:
        from_attributes = True

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    duration: Optional[time] = None
    price: Annotated[Decimal, Field(ge=0, max_digits=5, decimal_places=2)] = None
