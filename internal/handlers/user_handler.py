from ..services.user_service import UserService, AuthToken
from ..services.dynamodb_service import DynamoDBService, ItemCrudResponse

from data.models.user import User

class UserHandler:
    def __init__(self) -> None:
        self.user_service = UserService()

        self.dynamodb_service = DynamoDBService('User')

    def handle_create_user(self, user: User) -> ItemCrudResponse:
        return self.user_service.create_user(user)
    
    def handle_set_auth_token(self, user_id: str, auth_token: AuthToken):
        return self.user_service.set_auth_token(user_id, auth_token)
    
    def handle_get_user(self, user_id: str):
        return self.user_service.get_user(user_id)
    
    def handle_get_user_by_email(self, email: str):
        return self.user_service.get_user_by_email(email)
    
    def handle_confirm_user(self, user_id):
        return self.user_service.confirm_user(user_id)

