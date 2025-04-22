from pydantic import BaseModel, EmailStr
from typing import Optional

'''
Pydantic validation models for the users table endpoints
'''

class UserBase(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    phoneNumber: str
    is_admin: bool = False

class UserUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    phoneNumber: Optional[str] = None
    is_admin: Optional[bool] = None

class UserCreate(UserBase):
    password: str

class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

class UserResponse(UserBase):
    user_id: int
    roles: Optional[list[str]] = []

    class Config:
        from_attributes = True
