from pydantic import BaseModel
from datetime import datetime

'''
Pydantic validation classes for Messages
'''
# Message Base
class MessageBase(BaseModel):
    thread_id: int
    hasActiveMessage: bool
    text: str
    sender_id: int

# No additional fields needed to create message
class MessageCreate(MessageBase):
    pass 

class MessageActiveUpdate(BaseModel):
    hasActiveMessage: bool

# Add message_id and timeStamp in response
class MessageResponse(MessageBase):
    message_id: int
    timeStamp: datetime
    

    class Config:
        from_attributes = True
    