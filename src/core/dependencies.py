from typing import Annotated


from core.db import get_async_db_session
from fastapi import Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings

DBSessionDep = Annotated[AsyncSession, Depends(get_async_db_session)]

oauth_2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl=f"{settings.get_config()["keycloak_server_url"]}/protocol/openid-connect/token",
    authorizationUrl=f"{settings.get_config()["keycloak_server_url"]}/protocol/openid-connect/auth",
    refreshUrl=f"{settings.get_config()["keycloak_server_url"]}/protocol/openid-connect/token",
)