from typing import Optional, List
from sqlalchemy.orm import Session
from app.domain.entities.Package import Package
from app.domain.repositories.package_repository import IPackageRepository


class PackageRepository(IPackageRepository):
    """SQLAlchemy implementation of Package repository"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, package_id: int) -> Optional[Package]:
        return self.db.query(Package).filter(Package.id == package_id).first()

    def get_all(self) -> List[Package]:
        return self.db.query(Package).all()

    def create(self, package: Package) -> Package:
        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)
        return package

    def update(self, package: Package) -> Package:
        self.db.commit()
        self.db.refresh(package)
        return package

    def delete(self, package_id: int) -> bool:
        package = self.get_by_id(package_id)
        if package:
            self.db.delete(package)
            self.db.commit()
            return True
        return False

    def count(self) -> int:
        return self.db.query(Package).count()

