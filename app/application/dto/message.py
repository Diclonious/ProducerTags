from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MessageCreate(BaseModel):
    message_text: str


class MessageResponse(BaseModel):
    id: int
    order_id: int
    sender_id: int
    message_text: str
    created_at: datetime
    is_read: bool
    
    class Config:
        from_attributes = True

