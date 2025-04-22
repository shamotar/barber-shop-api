import time

from fastapi import HTTPException, status, Security
from keycloak.exceptions import KeycloakAuthenticationError
from core.config import settings
from auth.models import UserInfo
from keycloak import KeycloakOpenID, KeycloakOpenIDConnection, KeycloakAdmin
from modules.user.user_schema import UserCreate, UserUpdate
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


bearer_scheme = HTTPBearer()

class AuthService:

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
    def verify_token(token: str) -> UserInfo:
        try:
            token_info = AuthService.keycloak_openid.decode_token(
                token,
                validate=True,
            )
            # Check if the token is expired
            if token_info["exp"] < int(time.time()):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                )

            # Parses user roles into list
            roles = token_info.get("realm_access", {}).get("roles", [])


            this_user = UserInfo(
                id=token_info["sub"],
                username=token_info["preferred_username"],
                email=token_info.get("email"),
                full_name=token_info.get("name"),
                first_name=token_info.get("given_name"),
                last_name=token_info.get("family_name"),
                roles=roles,
            )

            return this_user
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    # Register a new user in Keycloak
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
            "credentials": [
                {"type": "password", "value": user.password, "temporary": False}
            ],
            "requiredActions": ["VERIFY_EMAIL"],
        }

        try:
            kc_user_id = AuthService.keycloak_admin.create_user(user_representation)
            return kc_user_id
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error creating user: {str(e)}"
            )

            

    def update_kc_user(user: UserUpdate):

        user_representation = {
            "username": user.email,
            "email": user.email,
            "firstName": user.firstName,
            "lastName": user.lastName,
        }

        try:
            user_id = AuthService.keycloak_admin.get_user_id(username=user.email)
            AuthService.keycloak_admin.update_user(
                user_id=user_id, payload=user_representation
            )
            return {"message": "User updated successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error updating user: {str(e)}"
            )
        
    def update_kc_user_password(kc_id: str, new_password: str):
        """
        Update the password of a user in Keycloak.
        Args:
            kc_id (str): The Keycloak ID of the user.
            new_password (str): The new password to set for the user.
        """
        try:
            AuthService.keycloak_admin.set_user_password(
                user_id=kc_id, password=new_password, temporary=False
            )
            return {"message": "Password updated successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error updating password: {str(e)}"
            )

    def delete_kc_user(user_email):
        try:
            user_id = AuthService.keycloak_admin.get_user_id(username=user_email)
            AuthService.keycloak_admin.delete_user(user_id=user_id)
            return {"message": "User deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error deleting user: {str(e)}"
            )

    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    ) -> UserInfo:
        """Extract and verify the token to retrieve user info."""
        token = credentials.credentials
        user_info = AuthService.verify_token(token)

        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return user_info
    
    def add_role_to_user(user_id: str, role_name: str):
        """
        Add a role to a user in Keycloak.
        """
        try:
            # Check if the role exists
            roles = AuthService.keycloak_admin.get_realm_roles()
            role_object = next(
                (role for role in roles if role["name"] == role_name), None
            )
            if not role_object:
                raise HTTPException(
                    status_code=404, detail=f"Role '{role_name}' not found"
                )
            # Assign the role to the user
            AuthService.keycloak_admin.assign_realm_roles(
                user_id=user_id, roles=[role_object]
            )
            
            return {"message": "Role added successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error adding role to user: {str(e)}"
            )
        
    def remove_role_from_user(user_id: str, role_name: str):
        """
        Remove a role from a user in Keycloak.
        """
        try:
            AuthService.keycloak_admin.delete_realm_roles_of_user(user_id=user_id, roles=[role_name])
            return {"message": "Role removed successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error removing role from user: {str(e)}"
            )
