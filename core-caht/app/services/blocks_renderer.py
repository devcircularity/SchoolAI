# app/services/blocks_renderer.py - Extended with button support

from typing import Any, Dict, List, Optional, Union
from app.schemas.blocks import *

def text(msg: str) -> TextBlock:
    """Create a text block with markdown support"""
    return TextBlock(type="text", text=msg)

def kpis(items: List[Dict[str, Any]]) -> KPIsBlock:
    """Create a KPIs block with interactive metric cards"""
    return KPIsBlock(type="kpis", items=[KPIItem(**i) for i in items])

def chart_xy(
    title: str, 
    chart_type: str, 
    x_field: str, 
    y_field: str, 
    series: List[Dict[str, Any]], 
    options: Optional[Dict[str, Any]] = None
) -> ChartBlock:
    """Create a bar/line/area chart"""
    return ChartBlock(type="chart", config=ChartConfigXY(
        title=title, 
        chartType=chart_type, 
        xField=x_field, 
        yField=y_field,
        series=[ChartSeries(**s) for s in series], 
        options=options or {}
    ))

def chart_pie(
    title: str, 
    label_field: str, 
    value_field: str, 
    data: List[Dict[str, Any]], 
    donut: bool = True, 
    options: Optional[Dict[str, Any]] = None
) -> ChartBlock:
    """Create a pie/donut chart"""
    return ChartBlock(type="chart", config=ChartConfigPie(
        title=title, 
        chartType="donut" if donut else "pie",
        labelField=label_field, 
        valueField=value_field, 
        data=data, 
        options=options or {}
    ))

def table(
    title: str, 
    columns: List[Dict[str, Any]], 
    rows: List[Dict[str, Any]],
    pagination: Optional[Dict[str, Any]] = None, 
    actions: Optional[List[Dict[str, Any]]] = None, 
    filters: Optional[List[Dict[str, Any]]] = None
) -> TableBlock:
    """Create a data table with sorting, pagination, and actions"""
    return TableBlock(type="table", config=TableConfig(
        title=title,
        columns=[TableColumn(**c) for c in columns],
        rows=rows,
        pagination=TablePagination(**pagination) if pagination else None,
        actions=[TableAction(**a) for a in (actions or [])],
        filters=[TableFilter(**f) for f in (filters or [])],
    ))

def timeline(items: List[Dict[str, Any]]) -> TimelineBlock:
    """Create a timeline/activity feed block"""
    return TimelineBlock(type="timeline", items=[TimelineItem(**i) for i in items])

def empty(title: str, hint: Optional[str] = None) -> EmptyBlock:
    """Create an empty state block"""
    return EmptyBlock(type="empty", title=title, hint=hint)

def error(title: str, detail: Optional[str] = None) -> ErrorBlock:
    """Create an error display block"""
    return ErrorBlock(type="error", title=title, detail=detail)

def file_download(
    name: str, 
    endpoint: str, 
    expires_at: Optional[str] = None
) -> FileDownloadBlock:
    """Create a file download block"""
    return FileDownloadBlock(
        type="file_download", 
        fileName=name, 
        endpoint=endpoint, 
        expiresAt=expires_at
    )

def status(items: List[Dict[str, Any]]) -> StatusBlock:
    """Create a status indicator block"""
    return StatusBlock(type="status", items=[StatusItem(**i) for i in items])

# NEW: Button and confirmation block renderers

def button(
    label: str, 
    action_type: str = "query", 
    payload: Optional[Dict[str, Any]] = None,
    variant: str = "primary", 
    size: str = "md", 
    icon: Optional[str] = None,
    disabled: bool = False, 
    endpoint: Optional[str] = None, 
    method: Optional[str] = None, 
    target: Optional[str] = None
) -> ButtonBlock:
    """Create a standalone button block"""
    action = ButtonAction(
        type=action_type,
        payload=payload or {},
        endpoint=endpoint,
        method=method,
        target=target
    )
    
    button_item = ButtonItem(
        label=label,
        variant=variant,
        size=size,
        icon=icon,
        disabled=disabled,
        action=action
    )
    
    return ButtonBlock(type="button", button=button_item)

def button_group(
    buttons: List[Dict[str, Any]], 
    layout: str = "horizontal", 
    align: str = "left"
) -> ButtonGroupBlock:
    """Create a group of buttons"""
    button_items = []
    for btn in buttons:
        action = ButtonAction(**btn.get("action", {}))
        button_item = ButtonItem(**{**btn, "action": action})
        button_items.append(button_item)
    
    return ButtonGroupBlock(
        type="button_group",
        buttons=button_items,
        layout=layout,
        align=align
    )

def confirmation_button(
    label: str, 
    title: str, 
    message: str, 
    action_type: str = "mutation",
    payload: Optional[Dict[str, Any]] = None, 
    variant: str = "danger", 
    size: str = "md", 
    icon: Optional[str] = None,
    confirm_label: str = "Confirm", 
    cancel_label: str = "Cancel",
    confirm_variant: str = "danger", 
    endpoint: Optional[str] = None,
    method: Optional[str] = None
) -> ConfirmationBlock:
    """Create a button with confirmation dialog"""
    action = ButtonAction(
        type=action_type,
        payload=payload or {},
        endpoint=endpoint,
        method=method
    )
    
    dialog = ConfirmationDialog(
        title=title,
        message=message,
        confirmLabel=confirm_label,
        cancelLabel=cancel_label,
        confirmVariant=confirm_variant
    )
    
    button_item = ConfirmationButton(
        label=label,
        variant=variant,
        size=size,
        icon=icon,
        dialog=dialog,
        action=action
    )
    
    return ConfirmationBlock(type="confirmation", button=button_item)

def action_panel(
    items: List[Dict[str, Any]], 
    title: Optional[str] = None, 
    columns: int = 1
) -> ActionPanelBlock:
    """Create an action panel with multiple action items"""
    panel_items = []
    for item in items:
        button_data = item.get("button", {})
        action = ButtonAction(**button_data.get("action", {}))
        button_item = ButtonItem(**{**button_data, "action": action})
        
        panel_item = ActionPanelItem(
            title=item["title"],
            description=item.get("description"),
            icon=item.get("icon"),
            button=button_item
        )
        panel_items.append(panel_item)
    
    return ActionPanelBlock(
        type="action_panel",
        title=title,
        items=panel_items,
        columns=columns
    )

# Utility functions for common data transformations
def currency_kpi(label: str, value: Union[int, float], variant: str = "primary") -> Dict[str, Any]:
    """Create a KES currency KPI item"""
    return {
        "label": label,
        "value": value,
        "format": "currency:KES",
        "variant": variant
    }

def percentage_kpi(label: str, value: Union[int, float], variant: str = "info") -> Dict[str, Any]:
    """Create a percentage KPI item"""
    return {
        "label": label,
        "value": value,
        "format": "percentage",
        "variant": variant
    }

def count_kpi(label: str, value: int, variant: str = "primary", action: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a count/number KPI item"""
    return {
        "label": label,
        "value": value,
        "format": "number",
        "variant": variant,
        "action": action
    }

# Common table column configurations
def currency_column(key: str, label: str, sortable: bool = True) -> Dict[str, Any]:
    """Create a currency table column"""
    return {
        "key": key,
        "label": label,
        "format": "currency:KES",
        "align": "right",
        "sortable": sortable
    }

def date_column(key: str, label: str, sortable: bool = True) -> Dict[str, Any]:
    """Create a date table column"""
    return {
        "key": key,
        "label": label,
        "format": "date",
        "sortable": sortable
    }

def status_column(key: str, label: str, status_map: Dict[str, str]) -> Dict[str, Any]:
    """Create a status badge column"""
    return {
        "key": key,
        "label": label,
        "badge": {"map": status_map}
    }

def action_row(row_data: Dict[str, Any], action_type: str = "query", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Add action to a table row"""
    row_with_action = row_data.copy()
    row_with_action["_action"] = {
        "type": action_type,
        "payload": payload or {}
    }
    return row_with_action

# Common button action helpers
def query_action(message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a query action for buttons"""
    return {
        "type": "query",
        "payload": {
            "message": message,
            "context": context or {}
        }
    }

def mutation_action(endpoint: str, method: str = "POST", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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

# Helper functions to create button items for button groups
def button_item(
    label: str,
    action_type: str = "query",
    payload: Optional[Dict[str, Any]] = None,
    variant: str = "primary",
    size: str = "md",
    icon: Optional[str] = None,
    disabled: bool = False,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    target: Optional[str] = None
) -> Dict[str, Any]:
    """Create a button item dictionary for use in button groups"""
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

def action_panel_item(
    title: str,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    button_label: str = "Execute",
    action_type: str = "query",
    payload: Optional[Dict[str, Any]] = None,
    button_variant: str = "primary"
) -> Dict[str, Any]:
    """Create an action panel item dictionary"""
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