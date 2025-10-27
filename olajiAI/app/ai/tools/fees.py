# app/ai/tools/fees.py - Fully compatible with your existing CoreHTTP

from typing import Dict, Any, List, Optional

class FeesClient:
    """HTTP client for fees-related operations - compatible with existing CoreHTTP"""
    
    def __init__(self, http):
        self.http = http  # your CoreHTTP instance

    async def list_structures(self, bearer: str, school_id: str) -> Dict[str, Any]:
        """Get all fee structures for the school"""
        # Use your existing CoreHTTP method signature
        r = await self.http.get("/fees/structures", bearer, school_id)
        return r

    async def list_items(self, bearer: str, school_id: str, fee_structure_id: str) -> Dict[str, Any]:
        """Get fee items for a specific structure"""
        r = await self.http.get(
            f"/fees/structures/{fee_structure_id}/items", 
            bearer, 
            school_id
        )
        return r

    async def patch_items(
        self, 
        bearer: str, 
        school_id: str, 
        fee_structure_id: str, 
        items: List[Dict[str, Any]], 
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update fee item prices"""
        payload = {"items": items}  # [{item_id?, item_name, amount}]
        
        # Use your existing CoreHTTP method signature
        r = await self.http.patch(
            f"/fees/structures/{fee_structure_id}/items",
            bearer,
            school_id,
            payload,
            idempotency_key  # Pass as final parameter if your method supports it
        )
        return r

    async def publish(
        self, 
        bearer: str, 
        school_id: str, 
        fee_structure_id: str, 
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publish a fee structure (locks it for invoice generation)"""
        # Use your existing CoreHTTP method signature
        r = await self.http.post(
            f"/fees/structures/{fee_structure_id}/publish",
            bearer,
            school_id,
            {},  # Empty payload for publish
            idempotency_key  # Pass as final parameter if your method supports it
        )
        return r

    async def pick_target_structure(
        self, 
        bearer: str, 
        school_id: str, 
        term: Optional[int] = None, 
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Auto-select the best fee structure to work with"""
        structs_response = await self.list_structures(bearer, school_id)
        
        # Extract data from response based on your CoreHTTP format
        if hasattr(structs_response, 'status_code'):
            if structs_response.status_code != 200:
                raise ValueError(f"Failed to fetch fee structures: {structs_response.status_code}")
            
            # Try to get JSON data
            if hasattr(structs_response, 'json'):
                structs_data = structs_response.json()
            else:
                # If no json method, check for content attribute
                structs_data = getattr(structs_response, 'content', [])
        else:
            # Assume it's already the parsed data
            structs_data = structs_response
        
        if not structs_data:
            raise ValueError("No fee structures found for this school")
        
        # Prefer exact term/year match
        if term and year:
            for s in structs_data:
                if s.get("term") == term and s.get("year") == year:
                    return s
        
        # Prefer default structure
        for s in structs_data:
            if s.get("is_default"):
                return s
        
        # Fallback: latest by (year, term)
        return sorted(
            structs_data, 
            key=lambda s: (s.get("year", 0), s.get("term", 0)), 
            reverse=True
        )[0]

    async def get_unpriced_items(
        self, 
        bearer: str, 
        school_id: str, 
        fee_structure_id: str
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Get items that don't have prices set (amount is NULL)"""
        items_response = await self.list_items(bearer, school_id, fee_structure_id)
        
        # Extract data from response based on your CoreHTTP format
        if hasattr(items_response, 'status_code'):
            if items_response.status_code != 200:
                raise ValueError(f"Failed to fetch fee items: {items_response.status_code}")
            
            # Try to get JSON data
            if hasattr(items_response, 'json'):
                items_data = items_response.json()
            else:
                # If no json method, check for content attribute
                items_data = getattr(items_response, 'content', [])
        else:
            # Assume it's already the parsed data
            items_data = items_response
        
        # Filter for unpriced items (amount is None/NULL)
        unpriced = [i for i in items_data if i.get("amount") is None]
        return unpriced, items_data

    async def generate_invoices(
        self,
        bearer: str,
        school_id: str,
        term: int,
        year: int,
        class_name: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate invoices for students"""
        payload = {
            "term": term,
            "year": year
        }
        
        if class_name:
            payload["class_name"] = class_name
        
        r = await self.http.post(
            "/invoices/generate",
            bearer,
            school_id,
            payload,
            idempotency_key
        )
        return r