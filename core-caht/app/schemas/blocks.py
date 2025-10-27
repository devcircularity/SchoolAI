# app/schemas/blocks.py - Complete fixed schema with ActionPanelBlock support

from typing import List, Literal, Optional, Union, Dict, Any
from pydantic import BaseModel

class TextBlock(BaseModel):
    type: Literal["text"]
    text: str

class KPIItem(BaseModel):
    label: str
    value: Union[int, float, str]
    icon: Optional[str] = None
    variant: Optional[Literal["primary", "success", "warning", "danger", "info"]] = None
    format: Optional[str] = None
    action: Optional[Dict[str, Any]] = None

class KPIsBlock(BaseModel):
    type: Literal["kpis"]
    items: List[KPIItem]

class ChartSeries(BaseModel):
    name: str
    data: List[Dict[str, Any]]

class ChartConfigXY(BaseModel):
    title: Optional[str] = None
    chartType: Literal["bar", "line", "area"]
    xField: str
    yField: str
    series: List[ChartSeries]
    options: Optional[Dict[str, Any]] = None

class ChartConfigPie(BaseModel):
    title: Optional[str] = None
    chartType: Literal["pie", "donut"]
    labelField: str
    valueField: str
    data: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = None

class ChartBlock(BaseModel):
    type: Literal["chart"]
    config: Union[ChartConfigXY, ChartConfigPie]

class TableColumn(BaseModel):
    key: str
    label: str
    width: Optional[int] = None
    sortable: Optional[bool] = None
    align: Optional[Literal["left", "center", "right"]] = None
    format: Optional[str] = None
    badge: Optional[Dict[str, Any]] = None

class TablePagination(BaseModel):
    mode: Literal["client", "server"] = "server"
    page: int = 1
    pageSize: int = 10
    total: Optional[int] = None
    nextCursor: Optional[str] = None

class TableAction(BaseModel):
    label: str
    type: Literal["export", "mutation", "route", "query"]
    endpoint: Optional[str] = None
    method: Optional[Literal["GET", "POST", "PUT", "DELETE"]] = None
    format: Optional[str] = None
    selectionRequired: Optional[bool] = None
    payload: Optional[Dict[str, Any]] = None
    target: Optional[str] = None

class TableFilter(BaseModel):
    type: Literal["select", "text", "daterange", "number"]
    key: str
    label: str
    options: Optional[List[Union[str, Dict[str, Any]]]] = None

class TableConfig(BaseModel):
    title: Optional[str] = None
    columns: List[TableColumn]
    rows: List[Dict[str, Any]]
    pagination: Optional[TablePagination] = None
    actions: Optional[List[TableAction]] = None
    filters: Optional[List[TableFilter]] = None

class TableBlock(BaseModel):
    type: Literal["table"]
    config: TableConfig

class TimelineItem(BaseModel):
    time: str
    icon: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class TimelineBlock(BaseModel):
    type: Literal["timeline"]
    items: List[TimelineItem]

class EmptyBlock(BaseModel):
    type: Literal["empty"]
    title: str
    hint: Optional[str] = None

class ErrorBlock(BaseModel):
    type: Literal["error"]
    title: str
    detail: Optional[str] = None

class FileDownloadBlock(BaseModel):
    type: Literal["file_download"]
    fileName: str
    endpoint: str
    expiresAt: Optional[str] = None

class StatusItem(BaseModel):
    label: str
    # FIXED: Extended to include common status names that get mapped to valid states
    state: Literal["ok", "warning", "error", "unknown", "success", "complete", "active", "ready", "good", "missing", "critical", "failed", "pending", "needs_setup", "inactive"]
    detail: Optional[str] = None

class StatusBlock(BaseModel):
    type: Literal["status"]
    items: List[StatusItem]

# Button and confirmation block types

class ButtonAction(BaseModel):
    type: Literal["query", "mutation", "route", "confirm", "download"]
    payload: Optional[Dict[str, Any]] = None
    endpoint: Optional[str] = None
    method: Optional[Literal["GET", "POST", "PUT", "DELETE"]] = None
    target: Optional[str] = None

class ButtonItem(BaseModel):
    label: str
    # FIXED: Added "info" variant to match the error
    variant: Optional[Literal["primary", "secondary", "success", "warning", "danger", "outline", "info"]] = "primary"
    size: Optional[Literal["sm", "md", "lg"]] = "md"
    icon: Optional[str] = None
    disabled: Optional[bool] = None
    loading: Optional[bool] = None
    action: ButtonAction

class ButtonBlock(BaseModel):
    type: Literal["button"]
    button: ButtonItem

class ButtonGroupBlock(BaseModel):
    type: Literal["button_group"]
    buttons: List[ButtonItem]
    layout: Optional[Literal["horizontal", "vertical"]] = "horizontal"
    align: Optional[Literal["left", "center", "right"]] = "left"

class ConfirmationDialog(BaseModel):
    title: str
    message: str
    confirmLabel: Optional[str] = "Confirm"
    cancelLabel: Optional[str] = "Cancel"
    confirmVariant: Optional[Literal["primary", "danger", "warning"]] = "primary"

class ConfirmationButton(BaseModel):
    label: str
    variant: Optional[Literal["primary", "secondary", "success", "warning", "danger", "outline", "info"]] = "primary"
    size: Optional[Literal["sm", "md", "lg"]] = "md"
    icon: Optional[str] = None
    disabled: Optional[bool] = None
    dialog: ConfirmationDialog
    action: ButtonAction

class ConfirmationBlock(BaseModel):
    type: Literal["confirmation"]
    button: ConfirmationButton

# CRITICAL: Forward declare ActionPanelItem to avoid circular reference
class ActionPanelItem(BaseModel):
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    button: ButtonItem

class ActionPanelBlock(BaseModel):
    type: Literal["action_panel"]
    title: Optional[str] = None
    items: List[ActionPanelItem]
    columns: Optional[Literal[1, 2, 3]] = 1

# Union type for all blocks - MUST include ActionPanelBlock
Block = Union[
    TextBlock, 
    KPIsBlock, 
    ChartBlock, 
    TableBlock, 
    TimelineBlock,
    EmptyBlock, 
    ErrorBlock, 
    FileDownloadBlock, 
    StatusBlock,
    ButtonBlock, 
    ButtonGroupBlock, 
    ConfirmationBlock, 
    ActionPanelBlock  # CRITICAL: This must be here
]