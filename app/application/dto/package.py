from pydantic import BaseModel
from typing import Optional


class PackageBase(BaseModel):
    name: str
    price: float
    delivery_days: int
    tag_count: int
    description: Optional[str] = None


class PackageCreate(PackageBase):
    pass


class PackageUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    delivery_days: Optional[int] = None
    tag_count: Optional[int] = None
    description: Optional[str] = None


class PackageResponse(PackageBase):
    id: int
    
    class Config:
        from_attributes = True

