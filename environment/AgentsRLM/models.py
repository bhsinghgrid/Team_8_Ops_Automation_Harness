from pydantic import BaseModel, ConfigDict
from typing import Dict, Any

class AgentInput(BaseModel):
    model_config = ConfigDict(extra='allow')
    
class AgentOutput(BaseModel):
    model_config = ConfigDict(extra='allow')
    result: Dict[str, Any] = {}
