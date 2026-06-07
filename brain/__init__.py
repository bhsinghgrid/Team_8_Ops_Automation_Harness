# Runbook_System_Final/engine/__init__.py
from .rlm_langgraph import RLMGraph
from .rlm import RecursiveLanguageModel
from .rlm_config import RLMConfig, PresetConfigs

def create_langgraph_rlm(preset="medium"):
    """Factory function to create a LangGraph-based RLM."""
    config = PresetConfigs.medium() if preset == "medium" else PresetConfigs.small()
    model = RecursiveLanguageModel(config=config)
    
    # We need a processing node that wraps the model
    from .rlm_langgraph import BaseProcessingNode
    
    class ModelProcessingNode(BaseProcessingNode):
        def __init__(self, model):
            self.model = model
        def process(self, text):
            return self.model.process_single(text)
            
    return RLMGraph(processing_node=ModelProcessingNode(model))
