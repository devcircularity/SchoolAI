# app/api/routes/fees.py - Complete implementation with all schemas

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import Optional, List
from pydantic import BaseModel

from app.core.db import get_db
from app.api.deps.tenancy import require_school
from app.models.fee import FeeStructure, FeeItem
# from app.models.class_model import Class  # Update this import to match your class model location

router = APIRouter(prefix="/fees", tags=["Fees"])

# Complete schemas
class FeeStructureOut(BaseModel):
    id: str
    name: str
    level: str
    term: int
    year: int
    is_default: bool
    is_published: bool

class FeeItemOut(BaseModel):
    id: str
    item_name: str
    amount: Optional[float]
    is_optional: bool
    class_id: Optional[str] = None
    class_name: Optional[str] = None

class FeeItemUpdate(BaseModel):
    item_id: Optional[str] = None
    item_name: str
    amount: float
    class_id: Optional[str] = None

class FeeItemCreate(BaseModel):
    item_name: str
    amount: Optional[float] = None
    is_optional: bool = False
    class_id: Optional[str] = None

class FeeItemsUpdateRequest(BaseModel):
    items: List[FeeItemUpdate]

class FeeItemsCreateRequest(BaseModel):
    items: List[FeeItemCreate]

class PublishResponse(BaseModel):
    message: str
    structure_id: str
    name: str
    term: int
    year: int

# MISSING ENDPOINT: List fee structures
@router.get("/structures", response_model=List[FeeStructureOut])
def list_structures(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
    level: Optional[str] = None,  # ✅ ADD THIS LINE
    term: Optional[int] = None,
    year: Optional[int] = None,
):
    """List fee structures with optional filtering by level, term, and year"""
    query = select(FeeStructure).where(FeeStructure.school_id == school_id)
    
    # ✅ ADD LEVEL FILTERING
    if level is not None:
        query = query.where(FeeStructure.level == level)
    if term is not None:
        query = query.where(FeeStructure.term == term)
    if year is not None:
        query = query.where(FeeStructure.year == year)
    
    rows = db.execute(
        query.order_by(FeeStructure.year.desc(), FeeStructure.term.desc())
    ).scalars().all()
    
    return [FeeStructureOut(
        id=r.id, 
        name=r.name, 
        level=r.level, 
        term=r.term, 
        year=r.year, 
        is_default=r.is_default,
        is_published=r.is_published
    ) for r in rows]

# ✅ ADD NEW ENDPOINT: Get available levels
@router.get("/structures/levels")
def get_available_levels(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Get all available CBC levels for this school"""
    
    # Get unique levels from fee structures
    levels = db.execute(
        select(FeeStructure.level).distinct().where(
            FeeStructure.school_id == school_id
        ).order_by(FeeStructure.level)
    ).scalars().all()
    
    # Map to CBC groups
    cbc_groups = {
        "Early Years Education (EYE)": ["PP1", "PP2"],
        "Lower Primary": ["Grade 1", "Grade 2", "Grade 3"],
        "Upper Primary": ["Grade 4", "Grade 5", "Grade 6"], 
        "Junior Secondary (JSS)": ["Grade 7", "Grade 8", "Grade 9"],
        "Senior Secondary": ["Grade 10", "Grade 11", "Grade 12"],
    }
    
    result = []
    for level in levels:
        group_name = "Unknown"
        for group, group_levels in cbc_groups.items():
            if level in group_levels:
                group_name = group
                break
        
        result.append({
            "label": level,
            "group_name": group_name
        })
    
    return result

@router.get("/structures/{structure_id}/items", response_model=List[FeeItemOut])
def get_fee_items(
    structure_id: str,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
    class_id: Optional[str] = None,
):
    """Get fee items for a structure, optionally filtered by class"""
    
    # Verify structure exists
    structure = db.execute(
        select(FeeStructure).where(
            and_(
                FeeStructure.id == structure_id,
                FeeStructure.school_id == school_id
            )
        )
    ).scalar_one_or_none()
    
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    
    # Build query for fee items
    query = select(FeeItem).where(FeeItem.fee_structure_id == structure_id)
    
    if class_id:
        # Get items for specific class OR school-wide items (class_id IS NULL)
        query = query.where(
            (FeeItem.class_id == class_id) | (FeeItem.class_id.is_(None))
        )
    
    items = db.execute(query).scalars().all()
    
    # Get class names for display (commented out until you confirm your Class model import)
    class_names = {}
    # if items:
    #     class_ids = [item.class_id for item in items if item.class_id]
    #     if class_ids:
    #         classes = db.execute(
    #             select(Class).where(Class.id.in_(class_ids))
    #         ).scalars().all()
    #         class_names = {cls.id: cls.name for cls in classes}
    
    return [FeeItemOut(
        id=item.id,
        item_name=item.item_name,
        amount=item.amount,
        is_optional=item.is_optional,
        class_id=item.class_id,
        class_name=class_names.get(item.class_id) if item.class_id else "All Classes"
    ) for item in items]

@router.post("/structures/{structure_id}/items")
def create_fee_items(
    structure_id: str,
    request: FeeItemsCreateRequest,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Create new fee items for a structure"""
    
    # Verify structure exists
    structure = db.execute(
        select(FeeStructure).where(
            and_(
                FeeStructure.id == structure_id,
                FeeStructure.school_id == school_id
            )
        )
    ).scalar_one_or_none()
    
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    
    if getattr(structure, 'is_published', False):
        raise HTTPException(status_code=400, detail="Cannot modify published fee structure")
    
    created_items = []
    
    for item_create in request.items:
        # Verify class exists if class_id provided (commented out until Class model confirmed)
        # if item_create.class_id:
        #     class_exists = db.execute(
        #         select(Class).where(
        #             and_(
        #                 Class.id == item_create.class_id,
        #                 Class.school_id == school_id
        #             )
        #         )
        #     ).scalar_one_or_none()
        #     
        #     if not class_exists:
        #         raise HTTPException(status_code=404, detail=f"Class not found: {item_create.class_id}")
        
        # Create fee item
        fee_item = FeeItem(
            school_id=school_id,
            fee_structure_id=structure_id,
            class_id=item_create.class_id,
            item_name=item_create.item_name,
            amount=item_create.amount,
            is_optional=item_create.is_optional
        )
        
        db.add(fee_item)
        created_items.append(fee_item)
    
    db.commit()
    
    return {
        "message": f"Created {len(created_items)} fee items",
        "created_items": [
            {
                "id": item.id,
                "item_name": item.item_name,
                "amount": float(item.amount) if item.amount else None,
                "class_id": item.class_id
            }
            for item in created_items
        ]
    }

@router.patch("/structures/{structure_id}/items")
def update_fee_items(
    structure_id: str,
    request: FeeItemsUpdateRequest,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Update fee item prices with class support"""
    
    # Verify structure exists
    structure = db.execute(
        select(FeeStructure).where(
            and_(
                FeeStructure.id == structure_id,
                FeeStructure.school_id == school_id
            )
        )
    ).scalar_one_or_none()
    
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    
    if getattr(structure, 'is_published', False):
        raise HTTPException(status_code=400, detail="Cannot modify published fee structure")
    
    updated_items = []
    
    for item_update in request.items:
        # Find item by ID, or by name+class combination
        item = None
        
        if item_update.item_id:
            item = db.execute(
                select(FeeItem).where(
                    and_(
                        FeeItem.id == item_update.item_id,
                        FeeItem.fee_structure_id == structure_id
                    )
                )
            ).scalar_one_or_none()
        else:
            # Find by name and class (or school-wide if no class specified)
            item = db.execute(
                select(FeeItem).where(
                    and_(
                        FeeItem.item_name == item_update.item_name,
                        FeeItem.fee_structure_id == structure_id,
                        FeeItem.class_id == item_update.class_id
                    )
                )
            ).scalar_one_or_none()
        
        if not item:
            class_desc = f" for class {item_update.class_id}" if item_update.class_id else " (school-wide)"
            raise HTTPException(
                status_code=404, 
                detail=f"Fee item not found: {item_update.item_name}{class_desc}"
            )
        
        # Update the amount
        item.amount = item_update.amount
        updated_items.append(item)
    
    db.commit()
    
    return {
        "message": f"Updated {len(updated_items)} fee items",
        "updated_items": [
            {
                "id": item.id,
                "item_name": item.item_name,
                "amount": float(item.amount) if item.amount else None,
                "class_id": item.class_id
            }
            for item in updated_items
        ]
    }

@router.get("/structures/{structure_id}/unpriced-items")
def get_unpriced_items(
    structure_id: str,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Get fee items that don't have prices set, grouped by class"""
    
    structure = db.execute(
        select(FeeStructure).where(
            and_(
                FeeStructure.id == structure_id,
                FeeStructure.school_id == school_id
            )
        )
    ).scalar_one_or_none()
    
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    
    # Get unpriced items
    unpriced_items = db.execute(
        select(FeeItem).where(
            and_(
                FeeItem.fee_structure_id == structure_id,
                FeeItem.amount.is_(None)
            )
        )
    ).scalars().all()
    
    # Group by class (simplified without Class model for now)
    grouped_items = {
        "school_wide": [],
        "by_class": {}
    }
    
    for item in unpriced_items:
        if item.class_id:
            class_name = f"Class {item.class_id}"  # Will be improved when Class model is available
            if class_name not in grouped_items["by_class"]:
                grouped_items["by_class"][class_name] = []
            grouped_items["by_class"][class_name].append({
                "id": item.id,
                "item_name": item.item_name,
                "is_optional": item.is_optional,
                "class_id": item.class_id
            })
        else:
            grouped_items["school_wide"].append({
                "id": item.id,
                "item_name": item.item_name,
                "is_optional": item.is_optional
            })
    
    return {
        "structure_id": structure_id,
        "structure_name": structure.name,
        "unpriced_count": len(unpriced_items),
        "grouped_items": grouped_items
    }

@router.post("/structures/{structure_id}/publish", response_model=PublishResponse)
def publish_fee_structure(
    structure_id: str,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Publish a fee structure (locks it for invoice generation)"""
    
    structure = db.execute(
        select(FeeStructure).where(
            and_(
                FeeStructure.id == structure_id,
                FeeStructure.school_id == school_id
            )
        )
    ).scalar_one_or_none()
    
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    
    if getattr(structure, 'is_published', False):
        return PublishResponse(
            message=f"Fee structure already published: {structure.name}",
            structure_id=structure.id,
            name=structure.name,
            term=structure.term,
            year=structure.year
        )
    
    # Check that all items have prices
    unpriced_items = db.execute(
        select(FeeItem).where(
            and_(
                FeeItem.fee_structure_id == structure_id,
                FeeItem.amount.is_(None)
            )
        )
    ).scalars().all()
    
    if unpriced_items:
        unpriced_details = []
        for item in unpriced_items:
            if item.class_id:
                unpriced_details.append(f"{item.item_name} (Class {item.class_id})")
            else:
                unpriced_details.append(f"{item.item_name} (All Classes)")
        
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish - unpriced items: {', '.join(unpriced_details)}"
        )
    
    # Publish the structure (if is_published field exists)
    if hasattr(structure, 'is_published'):
        structure.is_published = True
        db.commit()
    
    return PublishResponse(
        message=f"Published fee structure: {structure.name}",
        structure_id=structure.id,
        name=structure.name,
        term=structure.term,
        year=structure.year
    )