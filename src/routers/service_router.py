from typing import List
from fastapi import APIRouter, HTTPException

from core.dependencies import DBSessionDep
from modules.user.service_schema import ServiceBase, ServiceResponse, ServiceUpdate
from operations.service_operations import ServiceOperations


service_router = APIRouter(
    prefix="/api/v1/services",
    tags=["services"],
)

# POST endpoint to create a service
@service_router.post("", response_model=ServiceResponse)
async def create_service(service: ServiceBase, db_session: DBSessionDep):
    service_ops = ServiceOperations(db_session)
    response = await service_ops.create_service(service)

    return response


# GET endpoint to get all available services
@service_router.get("", response_model=List[ServiceResponse])
async def get_all_services(db_session: DBSessionDep):
    service_ops = ServiceOperations(db_session)
    response = await service_ops.get_all_services()
    
    return response

# PUT endpoint to update a service
@service_router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(db_session: DBSessionDep, service_id: int, service_details: ServiceUpdate):
    service_ops = ServiceOperations(db_session)
    response = await service_ops.update_service(service_id, service_details)

    return response

# DELETE endpoint to delete a service
@service_router.delete("/{service_id}", response_model=dict)
async def delete_service(db_session: DBSessionDep, service_id: int):
    service_ops = ServiceOperations(db_session)
    response = await service_ops.delete_service(service_id)

    if not response:
        raise HTTPException(
            status_code=400,
            detail="Service not found with provided ID"
        )
    
    return {"message": "Service deleted successfully"}
