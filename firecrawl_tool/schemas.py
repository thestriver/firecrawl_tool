from typing import Optional
from pydantic import BaseModel

class InputSchema(BaseModel):
    tool_name: str
    tool_input_data: str
    query: Optional[str] = None