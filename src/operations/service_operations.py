from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from modules.user.models import Service
from modules.user.service_schema import ServiceBase, ServiceResponse, ServiceUpdate
from fastapi import HTTPException

'''
Contains CRUD operations relating to services
'''
class ServiceOperations:

    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_service(self, service: ServiceBase) -> ServiceResponse:
        try:
            new_service = Service(**service.model_dump())
            self.db.add(new_service)
            await self.db.commit()
            await self.db.refresh(new_service)
            return new_service

        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
        
    async def get_all_services(self) -> List[ServiceResponse]:
        try:
            services = await self.db.execute(select(Service))
            return services.scalars().all()
        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
    
    async def update_service(self, service_id: int, service_details: ServiceUpdate) -> ServiceResponse:
        try:
            # Verify a service exists with the provided service ID
            service = await self.db.execute(select(Service).filter(Service.service_id == service_id))
            service_to_update = service.scalars().first()

            if not service_to_update:
                raise HTTPException(
                    status_code=400,
                    detail="Service not found with provided ID"
                )
        
            for key, value in service_details.model_dump(exclude_unset=True).items():
                setattr(service_to_update, key, value)

            await self.db.commit()
            await self.db.refresh(service_to_update)

            return service_to_update

        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )

    async def delete_service(self, service_id: int) -> bool:
        try:
            service = await self.db.execute(select(Service).filter(Service.service_id == service_id))
            service_to_delete = service.scalars().first()

            if not service_to_delete:
                return False

            await self.db.delete(service_to_delete)
            await self.db.commit()
            return True
        
        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )


        
        

    

