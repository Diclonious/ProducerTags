from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.User import User


class IUserRepository(ABC):
    

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        
        pass

    @abstractmethod
    def get_all(self) -> List[User]:
        
        pass

    @abstractmethod
    def get_admins(self) -> List[User]:
        
        pass

    @abstractmethod
    def create(self, user: User) -> User:
        
        pass

    @abstractmethod
    def update(self, user: User) -> User:
       
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        
        pass

