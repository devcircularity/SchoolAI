# app/schemas/fee.py - Complete updated schemas

from pydantic import BaseModel
from typing import Optional, List

class FeeStructureOut(BaseModel):
    id: str
    name: str
    level: str
    term: int
    year: int
    is_default: bool
    is_published: bool  # NEW: Include published status

class FeeItemOut(BaseModel):
    id: str
    item_name: str
    amount: Optional[float]
    is_optional: bool

class FeeItemUpdate(BaseModel):
    item_id: Optional[str] = None
    item_name: str
    amount: float

class FeeItemsUpdateRequest(BaseModel):
    items: List[FeeItemUpdate]

class PublishResponse(BaseModel):
    message: str
    structure_id: str
    name: str
    term: int
    year: int

class FeeStructureWithItems(BaseModel):
    id: str
    name: str
    level: str
    term: int
    year: int
    is_default: bool
    is_published: bool
    items: List[FeeItemOut]

class UnpricedItemsResponse(BaseModel):
    structure_id: str
    structure_name: str
    unpriced_count: int
    unpriced_items: List[dict]