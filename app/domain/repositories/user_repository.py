from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.User import User


class IUserRepository(ABC):
    """Abstract repository interface for User entity"""

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass

    @abstractmethod
    def get_all(self) -> List[User]:
        """Get all users"""
        pass

    @abstractmethod
    def get_admins(self) -> List[User]:
        """Get all admin users"""
        pass

    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user"""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update an existing user"""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete a user"""
        pass

