# app/api/routers/chat/blocks.py - Fixed with correct status states
from typing import Dict, List, Any, Optional

def text(content: str) -> Dict[str, Any]:
    """Create a text block"""
    return {
        "type": "text",
        "text": content
    }

def kpis(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a KPIs block with metric cards"""
    return {
        "type": "kpis", 
        "items": items
    }

def count_kpi(label: str, value: int, variant: str = "primary", action: Optional[Dict] = None) -> Dict[str, Any]:
    """Helper to create a count KPI item"""
    kpi = {
        "label": label,
        "value": value,
        "format": "integer",
        "variant": variant
    }
    if action:
        kpi["action"] = action
    return kpi

def currency_kpi(label: str, value: float, variant: str = "primary", action: Optional[Dict] = None) -> Dict[str, Any]:
    """Helper to create a currency KPI item"""
    kpi = {
        "label": label,
        "value": value,
        "format": "currency:KES",
        "variant": variant
    }
    if action:
        kpi["action"] = action
    return kpi

def table(title: str, columns: List[Dict], rows: List[Dict], 
          pagination: Optional[Dict] = None, actions: Optional[List] = None, 
          filters: Optional[List] = None) -> Dict[str, Any]:
    """Create a table block"""
    config = {
        "title": title,
        "columns": columns,
        "rows": rows
    }
    
    if pagination:
        config["pagination"] = pagination
    if actions:
        config["actions"] = actions
    if filters:
        config["filters"] = filters
        
    return {
        "type": "table",
        "config": config
    }

def status_column(key: str, label: str, status_map: Dict[str, str], 
                  sortable: bool = True, align: str = "center") -> Dict[str, Any]:
    """Helper to create a status badge column"""
    return {
        "key": key,
        "label": label,
        "sortable": sortable,
        "align": align,
        "badge": {
            "map": status_map
        }
    }

def action_row(row_data: Dict, action_type: str, payload: Dict) -> Dict[str, Any]:
    """Helper to add an action to a table row"""
    row_with_action = row_data.copy()
    row_with_action["_action"] = {
        "type": action_type,
        "payload": payload
    }
    return row_with_action

def chart_xy(title: str, chart_type: str, x_field: str, y_field: str, 
             series: List[Dict], options: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a bar/line/area chart block"""
    config = {
        "title": title,
        "chartType": chart_type,
        "xField": x_field,
        "yField": y_field,
        "series": series
    }
    
    if options:
        config["options"] = options
        
    return {
        "type": "chart",
        "config": config
    }

def chart_pie(title: str, chart_type: str, label_field: str, value_field: str,
              data: List[Dict], options: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a pie/donut chart block"""
    config = {
        "title": title,
        "chartType": chart_type,
        "labelField": label_field,
        "valueField": value_field,
        "data": data
    }
    
    if options:
        config["options"] = options
        
    return {
        "type": "chart",
        "config": config
    }

def timeline(items: List[Dict]) -> Dict[str, Any]:
    """Create a timeline block"""
    return {
        "type": "timeline",
        "items": items
    }

def timeline_item(time: str, title: str, subtitle: str = None, 
                  icon: str = "activity", meta: Optional[Dict] = None) -> Dict[str, Any]:
    """Helper to create a timeline item"""
    item = {
        "time": time,
        "icon": icon,
        "title": title
    }
    if subtitle:
        item["subtitle"] = subtitle
    if meta:
        item["meta"] = meta
    return item

def form(title: str, endpoint: str, method: str, fields: List[Dict]) -> Dict[str, Any]:
    """Create a form block"""
    return {
        "type": "form",
        "config": {
            "title": title,
            "submit": {
                "endpoint": endpoint,
                "method": method
            },
            "fields": fields
        }
    }

def form_field(key: str, label: str, field_type: str, required: bool = False,
               options: Optional[List] = None, endpoint: Optional[str] = None) -> Dict[str, Any]:
    """Helper to create a form field"""
    field = {
        "key": key,
        "label": label,
        "type": field_type,
        "required": required
    }
    if options:
        field["options"] = options
    if endpoint:
        field["endpoint"] = endpoint
    return field

def file_download(file_name: str, endpoint: str, expires_at: Optional[str] = None) -> Dict[str, Any]:
    """Create a file download block"""
    block = {
        "type": "file_download",
        "fileName": file_name,
        "endpoint": endpoint
    }
    if expires_at:
        block["expiresAt"] = expires_at
    return block

def status_block(items: List[Dict]) -> Dict[str, Any]:
    """Create a status block"""
    return {
        "type": "status",
        "items": items
    }

def status_item(label: str, state: str, detail: Optional[str] = None) -> Dict[str, Any]:
    """Helper to create a status item with automatic state mapping"""
    # Map common state names to valid Pydantic states
    state_mapping = {
        "success": "ok",
        "complete": "ok", 
        "active": "ok",
        "ready": "ok",
        "good": "ok",
        "warning": "warning",
        "needs_setup": "warning",
        "pending": "warning",
        "missing": "error",
        "critical": "error",
        "failed": "error",
        "error": "error",
        "unknown": "unknown",
        "inactive": "unknown"
    }
    
    # Convert state to valid Pydantic value
    valid_state = state_mapping.get(state.lower(), "unknown")
    
    item = {
        "label": label,
        "state": valid_state
    }
    if detail:
        item["detail"] = detail
    return item

def empty_state(title: str, hint: Optional[str] = None) -> Dict[str, Any]:
    """Create an empty state block"""
    block = {
        "type": "empty",
        "title": title
    }
    if hint:
        block["hint"] = hint
    return block

def error_block(title: str, detail: Optional[str] = None) -> Dict[str, Any]:
    """Create an error block"""
    block = {
        "type": "error", 
        "title": title
    }
    if detail:
        block["detail"] = detail
    return block

# Button and confirmation block builders

def button(label: str, action_type: str = "query", payload: Optional[Dict] = None,
           variant: str = "primary", size: str = "md", icon: Optional[str] = None,
           disabled: bool = False, endpoint: Optional[str] = None, 
           method: Optional[str] = None, target: Optional[str] = None) -> Dict[str, Any]:
    """Create a standalone button block"""
    action = {
        "type": action_type,
        "payload": payload or {}
    }
    
    if endpoint:
        action["endpoint"] = endpoint
    if method:
        action["method"] = method
    if target:
        action["target"] = target
    
    return {
        "type": "button",
        "button": {
            "label": label,
            "variant": variant,
            "size": size,
            "icon": icon,
            "disabled": disabled,
            "action": action
        }
    }

def button_group(buttons: List[Dict], layout: str = "horizontal", 
                 align: str = "left") -> Dict[str, Any]:
    """Create a group of buttons"""
    return {
        "type": "button_group",
        "buttons": buttons,
        "layout": layout,
        "align": align
    }

def button_item(label: str, action_type: str = "query", payload: Optional[Dict] = None,
                variant: str = "primary", size: str = "md", icon: Optional[str] = None,
                disabled: bool = False, endpoint: Optional[str] = None, 
                method: Optional[str] = None, target: Optional[str] = None) -> Dict[str, Any]:
    """Helper to create a button item for button groups"""
    action = {
        "type": action_type,
        "payload": payload or {}
    }
    
    if endpoint:
        action["endpoint"] = endpoint
    if method:
        action["method"] = method
    if target:
        action["target"] = target
    
    return {
        "label": label,
        "variant": variant,
        "size": size,
        "icon": icon,
        "disabled": disabled,
        "action": action
    }

def confirmation_button(label: str, title: str, message: str, action_type: str = "mutation",
                       payload: Optional[Dict] = None, variant: str = "danger", 
                       size: str = "md", icon: Optional[str] = None,
                       confirm_label: str = "Confirm", cancel_label: str = "Cancel",
                       confirm_variant: str = "danger", endpoint: Optional[str] = None,
                       method: Optional[str] = None) -> Dict[str, Any]:
    """Create a button with confirmation dialog"""
    action = {
        "type": action_type,
        "payload": payload or {}
    }
    
    if endpoint:
        action["endpoint"] = endpoint
    if method:
        action["method"] = method
    
    return {
        "type": "confirmation",
        "button": {
            "label": label,
            "variant": variant,
            "size": size,
            "icon": icon,
            "dialog": {
                "title": title,
                "message": message,
                "confirmLabel": confirm_label,
                "cancelLabel": cancel_label,
                "confirmVariant": confirm_variant
            },
            "action": action
        }
    }

def action_panel(items: List[Dict], title: Optional[str] = None, 
                 columns: int = 1) -> Dict[str, Any]:
    """Create an action panel with multiple action items"""
    return {
        "type": "action_panel",
        "title": title,
        "items": items,
        "columns": columns
    }

def action_panel_item(title: str, description: Optional[str] = None, 
                      icon: Optional[str] = None, button_label: str = "Execute",
                      action_type: str = "query", payload: Optional[Dict] = None,
                      button_variant: str = "primary") -> Dict[str, Any]:
    """Helper to create an action panel item"""
    # Map 'info' variant to valid variant (since we added it to schema)
    if button_variant == "info":
        button_variant = "info"  # Now valid in schema
    
    return {
        "title": title,
        "description": description,
        "icon": icon,
        "button": {
            "label": button_label,
            "variant": button_variant,
            "action": {
                "type": action_type,
                "payload": payload or {}
            }
        }
    }

# Common action helpers
def query_action(message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a query action for buttons"""
    return {
        "type": "query",
        "payload": {
            "message": message,
            "context": context or {}
        }
    }

def mutation_action(endpoint: str, method: str = "POST", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a mutation action for buttons"""
    return {
        "type": "mutation",
        "endpoint": endpoint,
        "method": method,
        "payload": data or {}
    }

def route_action(target: str) -> Dict[str, Any]:
    """Create a route navigation action"""
    return {
        "type": "route",
        "target": target
    }

def download_action(endpoint: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Create a download action"""
    return {
        "type": "download",
        "endpoint": endpoint,
        "payload": {"filename": filename} if filename else {}
    }