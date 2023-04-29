from data.models.user import User, AuthToken

from .dynamodb_service import DynamoDBService, ItemCrudResponse, Key

from .s3_service import S3Service

class UserService:
    def __init__(self, user: User = None) -> None:
        self.user = user

        self.dynamodb_service = DynamoDBService('User')

        self.s3_service = S3Service()

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

    def get_user_by_username(self, username):
        query_key = Key('username').eq(username)

        return self.dynamodb_service.scan_table(query_key, limit=1)
    
    def get_avatar(self, user_id: str):
        if not user_id:
            return ItemCrudResponse(
                Item={},
                success=False,
                exception=Exception(message='User ID is required')
            )
        
        if user_id == 'default':
            return self.s3_service.get_default_user_avatar_url()

        result = self.dynamodb_service.get_item(user_id)

        if not result.success or result.Item == {}:
            return result
        
        user = result.Item

        if 'avatar_url' not in user:
            return ItemCrudResponse(
                Item={},
                success=False,
                exception=Exception(message='User does not have an avatar')
            )
        
        return user['avatar_url']
    
    def set_avatar(self, user_id: str, file: bytes):
        # Upload avatar to S3
        upload_response_url = self.s3_service.upload_avatar(user_id, file)

        # get user from user_id
        result = self.dynamodb_service.get_item(user_id)

        if not result.success or result.Item == {} or not upload_response_url:
            return result
        
        # update user with new avatar_url
        user = result.Item
        user['avatar_url'] = upload_response_url
        update_result = self.dynamodb_service.update_item(user)

        if not update_result.success:
            return update_result

        return upload_response_url
