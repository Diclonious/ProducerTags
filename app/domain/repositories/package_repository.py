from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.Package import Package


class IPackageRepository(ABC):
   

    @abstractmethod
    def get_by_id(self, package_id: int) -> Optional[Package]:
        
        pass

    @abstractmethod
    def get_all(self) -> List[Package]:
        
        pass

    @abstractmethod
    def create(self, package: Package) -> Package:
        
        pass

    @abstractmethod
    def update(self, package: Package) -> Package:
        
        pass

    @abstractmethod
    def delete(self, package_id: int) -> bool:
        
        pass

    @abstractmethod
    def count(self) -> int:
        
        pass

