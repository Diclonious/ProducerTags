from typing import Optional
from app.domain.entities.User import User
from app.domain.repositories.user_repository import IUserRepository
from app.application.dto.user import UserCreate, UserLogin


class AuthUseCase:
   

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = self.user_repository.get_by_username(login_data.username)
        if user and user.check_password(login_data.password):
            return user
        return None

    def create_user(self, user_data: UserCreate) -> User:
       
        if self.user_repository.get_by_username(user_data.username):
            raise ValueError("Username already exists")

        if self.user_repository.get_by_email(user_data.email):
            raise ValueError("Email already exists")

        user = User(
            username=user_data.username,
            email=user_data.email,
            is_admin=user_data.is_admin
        )
        user.set_password(user_data.password)

        return self.user_repository.create(user)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
       
        return self.user_repository.get_by_id(user_id)

