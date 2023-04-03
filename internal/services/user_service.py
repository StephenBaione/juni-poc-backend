from data.models.user import User, AuthToken

from .dynamodb_service import DynamoDBService, ItemCrudResponse, Key

class UserService:
    def __init__(self, user: User = None) -> None:
        self.user = user

        self.dynamodb_service = DynamoDBService('User')

    def create_user(self, user: User) -> ItemCrudResponse:
        # Check if user exists
        user = User.set_id(user)
        _id = user.id

        result = self.dynamodb_service.get_item(_id)

        if result.success and result.Item != {}:
            return ItemCrudResponse(
                Item={},
                success=False,
                exception=Exception(message='User Already Exists')
            )
        
        # Create user
        return self.dynamodb_service.update_item(user)
    
    def set_auth_token(self, user_id: str, auth_token: AuthToken):
        filter_expression = Key('id').eq(user_id)
        result = self.dynamodb_service.scan_table(filter_expression, limit=1)

        if not result.success or result.Item == []:
            return result
        
        user = result.Item[0]
        user['auth_token_set'] = True
        user['auth_token'] = dict(auth_token)
        user['confirmed'] = True

        return self.dynamodb_service.update_item(user)
    
    def get_user(self, user_id: str):
        return self.dynamodb_service.get_item(user_id)
    
    def get_user_by_email(self, email: str):
        query_key = Key('email').eq(email)

        return self.dynamodb_service.scan_table(query_key, limit=1)
    
    def confirm_user(self, user_id):
        result = self.dynamodb_service.get_item(user_id)

        if not result.success or result.Item == {}:
            return result
        
        user = result.Item
        user['confirmed'] = True

        return self.dynamodb_service.update_item(user)
