from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class PaymentInfo(BaseModel):
    card_number: str = Field(..., min_length=13, max_length=19)
    card_holder: str = Field(..., min_length=3)
    card_expiry: str = Field(..., pattern=r'^\d{2}/\d{2}$')
    card_cvv: str = Field(..., min_length=3, max_length=4)
    
    @field_validator('card_number')
    @classmethod
    def clean_card_number(cls, v):
        return v.replace(" ", "").replace("-", "")


class OrderCreate(BaseModel):
    package_id: int
    details: Optional[str] = None
    tags: List[str] = []
    moods: List[str] = []
    payment: PaymentInfo


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    details: Optional[str] = None
    response: Optional[str] = None
    review: Optional[int] = None
    review_text: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    user_id: int
    package_id: int
    details: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str
    response: Optional[str] = None
    delivery_file: Optional[str] = None
    review: Optional[int] = None
    review_text: Optional[str] = None
    completed_date: Optional[datetime] = None
    cancelled_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OrderDeliver(BaseModel):
    response_text: str
    files: List[str]  # File paths


class OrderReview(BaseModel):
    review: int = Field(..., ge=1, le=5)
    review_text: str


class ResolutionRequest(BaseModel):
    request_type: str  # 'revision', 'cancellation', 'extend_delivery', 'dispute'
    message: Optional[str] = None
    dispute_message: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancellation_message: Optional[str] = None
    extension_days: Optional[int] = None
    extension_reason: Optional[str] = None


class RevisionRequest(BaseModel):
    revision_text: str

