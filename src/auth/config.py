from pydantic_settings import BaseSettings
from pydantic import Field
from keycloak import KeycloakOpenID
from dotenv import load_dotenv
import os

# Load enviroment variables 
load_dotenv()

class Settings(BaseSettings):
    keycloak_server_url: str = Field(os.getenv("KEYCLOAK_SERVER_URL"))
    keycloak_realm: str = Field(os.getenv("KEYCLOAK_REALM"))
    keycloak_client_id: str = Field(os.getenv("KEYCLOAK_API_CLIENT_ID"))
    keycloak_client_secret: str = Field(os.getenv("KEYCLOAK_API_SECRET"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak_server_url,
    realm_name=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
    client_secret_key=settings.keycloak_client_secret,
)

def get_openid_config():
    return keycloak_openid.well_known()