from typing import Any, Dict
from app.core.http import CoreHTTP

class ToolContext:
    def __init__(self, http: CoreHTTP, school_id: str, bearer: str, message_id: str | None):
        self.http = http
        self.school_id = school_id
        self.bearer = bearer
        self.message_id = message_id

class ToolResult(Dict[str, Any]):
    pass
