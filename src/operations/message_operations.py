import logging
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from modules.message_schema import MessageActiveUpdate, MessageCreate, MessageResponse
from modules.user.models import Message, Thread
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("message_operations")
logger.setLevel(logging.ERROR)

class MessageOperations:

    def __init__(self, db: AsyncSession):
        self.db = db
    

    # Create a new message
    async def create_message(self, message: MessageCreate) -> MessageResponse:
        try:
            # Check to ensure thread exists
            existing_thread = await self.db.execute(select(Thread).filter(Thread.thread_id == message.thread_id))
            existing_thread_result = existing_thread.scalars().first()

            if not existing_thread_result:
                raise HTTPException(
                    status_code=400,
                    detail=f"No thread exists with ID: {message.thread_id}" 
                )
            
            # Create new message using provided details
            new_message = Message(
                thread_id = message.thread_id,
                hasActiveMessage = message.hasActiveMessage,
                text = message.text,
                sender_id = message.sender_id
            )

            self.db.add(new_message)
            await self.db.commit()
            await self.db.refresh(new_message)

            # Return created message details
            return new_message

        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred during message creation"
            )
    
    # Update a message's 'hasActiveMessage' boolean
    async def update_hasActiveMessage_boolean(self, message_id: int, message_update: MessageActiveUpdate) -> MessageResponse:
        try:
            # Ensure message exists in DB before attempting to update
            message = await self.db.execute(select(Message).filter(Message.message_id == message_id))
            message_result = message.scalars().first()

            if not message_result:
                raise HTTPException(
                    status_code=404,
                    detail=f"No message found with ID: {message_id}"
                )
            
            # Update the boolean using boolean provided in message_update argument
            message_result.hasActiveMessage = message_update.hasActiveMessage

            await self.db.commit()
            await self.db.refresh(message_result)

            return message_result


        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unknown error occurred while updating 'hasActiveMessage' boolean"
            )
    
            
