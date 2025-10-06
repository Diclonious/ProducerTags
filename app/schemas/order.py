from pydantic import BaseModel, EmailStr
from typing import Optional

class OrderBase(BaseModel):
    name: str
    email: EmailStr
    details: Optional[str] = None