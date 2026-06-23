import asyncio
import json
import logging
import os
import sys

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from base_agent import BaseAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReleaseAgent(BaseAgent):
    """
    A simple agent that simulates the final release or deployment of a fix
    after it has been approved.
    """
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        super().__init__(model_name=model_name, enable_deep_rca=False)

    def get_system_prompt(self) -> str:
        return """You are a Release Agent. Your task is to provide a final confirmation that a fix has been deployed.
Based on the final approval, generate a success message.
Return your confirmation in a structured JSON format.
"""

async def main():
    agent = ReleaseAgent()
    approval_signal = {"status": "Deployment Approved", "final_ndcg": 0.92}
    result = await agent.run_agent(approval_signal)
    print("Agent Output:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
