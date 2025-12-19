"""Dependency injection container for application services"""
from sqlalchemy.orm import Session
from pathlib import Path

from app.infrastructure.repositories.user_repository_impl import UserRepository
from app.infrastructure.repositories.order_repository_impl import OrderRepository
from app.infrastructure.repositories.package_repository_impl import PackageRepository
from app.infrastructure.repositories.message_repository_impl import MessageRepository
from app.infrastructure.repositories.notification_repository_impl import NotificationRepository
from app.infrastructure.storage.file_storage import FileStorageService
from app.application.use_cases.auth_use_case import AuthUseCase
from app.application.use_cases.order_use_case import OrderUseCase
from app.application.use_cases.package_use_case import PackageUseCase
from app.application.use_cases.message_use_case import MessageUseCase
from app.application.use_cases.notification_use_case import NotificationUseCase
from app.application.use_cases.analytics_use_case import AnalyticsUseCase


class ServiceContainer:
 

    def __init__(self, db: Session, upload_dir: Path):
        self.db = db
        self.upload_dir = upload_dir


        self.user_repository = UserRepository(db)
        self.order_repository = OrderRepository(db)
        self.package_repository = PackageRepository(db)
        self.message_repository = MessageRepository(db)
        self.notification_repository = NotificationRepository(db)


        self.file_storage = FileStorageService(upload_dir)


        self.auth_use_case = AuthUseCase(self.user_repository)
        self.order_use_case = OrderUseCase(
            self.order_repository,
            self.package_repository,
            self.user_repository,
            self.notification_repository,
            db=db
        )
        self.package_use_case = PackageUseCase(self.package_repository)
        self.message_use_case = MessageUseCase(
            self.message_repository,
            self.order_repository
        )
        self.notification_use_case = NotificationUseCase(self.notification_repository)
        self.analytics_use_case = AnalyticsUseCase(self.order_repository)
