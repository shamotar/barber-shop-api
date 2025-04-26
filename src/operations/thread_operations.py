from typing import List
from fastapi import HTTPException
from sqlalchemy import or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from modules.thread_schema import ThreadCreate, ThreadResponse
from sqlalchemy.exc import SQLAlchemyError
import logging
from modules.user.models import Message, Thread, User
from modules.message_schema import MessageResponse

logger = logging.getLogger("thread_operations")
logger.setLevel(logging.ERROR)
                
class ThreadOperations:

    def __init__(self, db: AsyncSession):
        self.db = db

    # Create a new thread
    async def create_thread(self, thread: ThreadCreate) -> ThreadResponse:
        try:
            
            # Check that provides user IDs are valid

            existing_user_one = await self.db.execute(select(User).filter(User.user_id == thread.receivingUser))
            existing_user_one_result = existing_user_one.scalars().first()

            if not existing_user_one_result:
                raise HTTPException(
                    status_code=400,
                    detail=f"No user found with ID: {thread.receivingUser}"
                )
            
            existing_user_two = await self.db.execute(select(User).filter(User.user_id == thread.sendingUser))
            existing_user_two_result = existing_user_two.scalars().first()

            if not existing_user_two_result:
                raise HTTPException(
                    status_code=400,
                    detail=f"No user found with ID: {thread.sendingUser}"
                )
            
            # Create, commit, and return the thread

            new_thread = Thread(
                receivingUser=thread.receivingUser,
                sendingUser=thread.sendingUser,
            )
            self.db.add(new_thread)
            await self.db.commit()
            await self.db.refresh(new_thread)

            await self.db.refresh(existing_user_one_result)
            await self.db.refresh(existing_user_two_result)

            return ThreadResponse(
                thread_id=new_thread.thread_id,
                receivingUser=new_thread.receiving_user.user_id,
                sendingUser=new_thread.sending_user.user_id
            )
        
        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred during thread creation"
            )
    
    # Return threads were the user is both 'sendingUser' and 'recievingUser'
    # in order to properly display both sides of the conversation
    async def get_threads_by_user_id(self, logged_user_id: int, other_user_id: int, page: int, limit: int) -> List[ThreadResponse]:
        try:
            
            #Check to make sure both users IDs are valid

            logged_in_user = await self.db.execute(select(User).filter(User.user_id == logged_user_id))
            logged_in_user_result = logged_in_user.scalars().first()

            if not logged_in_user_result:
                raise HTTPException(
                    status_code=400,
                    detail=f"No user found with ID: {logged_user_id}"
                )
            
            other_user = await self.db.execute(select(User).filter(User.user_id == other_user_id))
            other_user_result = other_user.scalars().first()

            if not other_user:
                raise HTTPException(
                    status_code=400,
                    detail=f"No user found with ID: {other_user_id}"
                )
            
            # Set offset based off page requested by client
            offset = (page - 1) * limit
            
            # Retrieve threads from DB for both users

            threads = await self.db.execute(
            select(Thread).filter(
                    (
                        (Thread.receivingUser == logged_user_id) & (Thread.sendingUser == other_user_id) |
                        (Thread.receivingUser == other_user_id) & (Thread.sendingUser == logged_user_id)
                    )
                ).limit(limit).offset(offset)
            )
        
            threads_results = threads.scalars().all()

            thread_responses = []
            
            # Retrieve all messages from each thread, newest first
            for thread in threads_results:
                messages = await self.db.execute(
                    select(Message)
                    .filter(Message.thread_id == thread.thread_id)
                    .order_by(desc(Message.timeStamp))
                )
                messages_results = messages.scalars().all()

                thread_response = ThreadResponse(
                    thread_id=thread.thread_id,
                    receivingUser=thread.receivingUser,
                    sendingUser=thread.sendingUser,
                    # messages come back newest→oldest, your front end then sorts oldest→newest
                    messages=[MessageResponse.model_validate(message) for message in messages_results]
                )
                thread_responses.append(thread_response)
            
            return thread_responses
            

        
        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred during retrieval"
            )
    
    async def get_all_threads_by_user_id(self, user_id: int, page: int, limit: int) -> List[ThreadResponse]:
        try:
            # Make sure user_id links to a valid user
            user = await self.db.execute(select(User).filter(User.user_id == user_id))
            user_result = user.scalars().first()

            if not user_result:
                raise HTTPException(
                    status_code=400,
                    detail=f"No user found with ID: {user_id}"
                )
            
            threads = await self.db.execute(select(Thread).filter(
                (Thread.receivingUser == user_id) | (Thread.sendingUser == user_id)
            ))

            thread_results = threads.scalars().all()
            
            thread_responses = []

            # Set offset based off page requested by client
            offset = (page - 1) * limit

            for thread in thread_results:
                messages = await self.db.execute(
                    select(Message)
                    .filter(Message.thread_id == thread.thread_id)
                    .order_by(desc(Message.timeStamp))
                    .limit(limit)
                    .offset(offset)
                )
                messages_results = messages.scalars().all()


                 # Craft response, including thread details and all messages for each associated thread

                thread_response = ThreadResponse(
                    thread_id=thread.thread_id,
                    receivingUser=thread.receivingUser,
                    sendingUser=thread.sendingUser,
                    messages=[MessageResponse.model_validate(message) for message in messages_results]
                )
                thread_responses.append(thread_response)
            
            return thread_responses

        except SQLAlchemyError as e:
            logger.error(e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred during retrieval"
            )
