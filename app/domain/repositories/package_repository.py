from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.Package import Package


class IPackageRepository(ABC):
    """Abstract repository interface for Package entity"""
    
    @abstractmethod
    def get_by_id(self, package_id: int) -> Optional[Package]:
        """Get package by ID"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Package]:
        """Get all packages"""
        pass
    
    @abstractmethod
    def create(self, package: Package) -> Package:
        """Create a new package"""
        pass
    
    @abstractmethod
    def update(self, package: Package) -> Package:
        """Update an existing package"""
        pass
    
    @abstractmethod
    def delete(self, package_id: int) -> bool:
        """Delete a package"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total count of packages"""
        pass

