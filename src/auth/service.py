from fastapi import HTTPException, status
from keycloak.exceptions import KeycloakAuthenticationError
from core.config import settings
from auth.models import UserInfo
from keycloak import KeycloakOpenID, KeycloakOpenIDConnection, KeycloakAdmin
from modules.user.user_schema import UserCreate



class AuthService():
    # Keycloak connection using credentials from core/config/settings
    keycloak_openid = KeycloakOpenID(
        server_url=settings.get_config()["keycloak_server_url"],
        realm_name=settings.get_config()["keycloak_realm"],
        client_id=settings.get_config()["keycloak_api_client_id"],
        client_secret_key=settings.get_config()["keycloak_api_secret"],
        )
    
    # Keycloak Admin (For User Management)
    keycloak_admin_connection = KeycloakOpenIDConnection(
        server_url=settings.get_config()["keycloak_server_url"],
        username=settings.get_config()["keycloak_admin_username"],
        password=settings.get_config()["keycloak_admin_password"],
        realm_name=settings.get_config()["keycloak_realm"],
        client_id=settings.get_config()["keycloak_api_client_id"],
        client_secret_key=settings.get_config()["keycloak_api_secret"],
        verify=True,
    )
    keycloak_admin = KeycloakAdmin(connection=keycloak_admin_connection)


    # Checks username and password against Keycloak DB and return JWT
    @staticmethod
    def authenticate_user(username: str, password: str) -> str:
        """
        Authenticate the user using Keycloak and return an access token.
        """
        try:
            token = AuthService.keycloak_openid.token(username, password)
            return token["access_token"]
        except KeycloakAuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

    # Verifies token against Keycloak and UserInfo model and returns user info
    @staticmethod
    def verify_token(token: str) -> UserInfo:
        """
        Verify the given token and return user information.
        """
        try:
            user_info = AuthService.keycloak_openid.userinfo(token)
            print(user_info)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
            return UserInfo(
                username=user_info["preferred_username"],
                email=user_info.get("email"),
                full_name=user_info.get("name"),
                first_name=user_info.get("given_name"),
                last_name=user_info.get("family_name"), 
)           
        except KeycloakAuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        
    # Register a new user in Keycloak
    @staticmethod
    def register_kc_user(user: UserCreate):
        """
        Register a new user in Keycloak.
        """
        
        user_representation = {
            "username": user.email,
            "email": user.email,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "enabled": True,
            "credentials": [{"type": "password", "value": user.password, "temporary": False}],
        }



        try:
            AuthService.keycloak_admin.create_user(user_representation)
            return {"message": "User created successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error creating user: {str(e)}"
            )