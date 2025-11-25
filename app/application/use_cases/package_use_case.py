from typing import List, Optional
from app.domain.entities.Package import Package
from app.domain.repositories.package_repository import IPackageRepository
from app.application.dto.package import PackageCreate, PackageUpdate


class PackageUseCase:
    """Use case for package operations"""

    def __init__(self, package_repository: IPackageRepository):
        self.package_repository = package_repository

    def get_all_packages(self) -> List[Package]:
        """Get all packages"""
        return self.package_repository.get_all()

    def get_package_by_id(self, package_id: int) -> Optional[Package]:
        """Get package by ID"""
        return self.package_repository.get_by_id(package_id)

    def create_package(self, package_data: PackageCreate) -> Package:
        """Create a new package"""
        package = Package(
            name=package_data.name,
            price=package_data.price,
            delivery_days=package_data.delivery_days,
            tag_count=package_data.tag_count,
            description=package_data.description
        )
        return self.package_repository.create(package)

    def update_package(self, package_id: int, package_data: PackageUpdate) -> Package:
        """Update an existing package"""
        package = self.package_repository.get_by_id(package_id)
        if not package:
            raise ValueError("Package not found")

        if package_data.name is not None:
            package.name = package_data.name
        if package_data.price is not None:
            package.price = package_data.price
        if package_data.delivery_days is not None:
            package.delivery_days = package_data.delivery_days
        if package_data.tag_count is not None:
            package.tag_count = package_data.tag_count
        if package_data.description is not None:
            package.description = package_data.description

        return self.package_repository.update(package)

    def delete_package(self, package_id: int) -> bool:
        """Delete a package"""
        return self.package_repository.delete(package_id)

