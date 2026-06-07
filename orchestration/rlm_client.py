# Runbook_System_Final/orchestration/rlm_client.py
"""
A simple, easy-to-understand RLM (Reasoning and Language Model) client.
This acts as the "brain" for our agents, allowing them to reason about data.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from google import genai
from google.generativeai import types
from google.generativeai.generative_models import GenerativeModel

# NOTE: This client currently directly uses Google GenAI. 
# For full RLM functionality (decomposition, composition, self-critique, cache),
# you should integrate with the LangGraph-based RLM in `Runbook_System_Final/brain/rlm_langgraph.py`.
# This RLMClient would then wrap that LangGraph RLM for external calls.

class RLMClient:
    def __init__(self):
        self._load_env_file()
        self.api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("⚠️ [RLMClient WARNING]: GEMINI_API_KEY not found in .env. RLM will return fallback data.")
        # Use genai.GenerativeModel for Gemini 2.5 Flash
        self.client = GenerativeModel(model_name='gemini-2.5-flash') if self.api_key else None
        # Configure the client for JSON output and low temperature
        if self.client:
            self.generation_config = types.GenerationConfig(
                # response_mime_type="application/json",
                temperature=0.1,
            )
        else:
            self.generation_config = None # No config if no client


    def _load_env_file(self):
        """Loads environment variables from the .env file in the project root."""
        # Adjust path to find .env in the root of the Agents folder
        env_path = Path(__file__).resolve().parents[3] / ".env" # Go up 3 levels to '/Users/bhsingh/Documents/Capstone_Final/Agents/.env'
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'").strip('"')
        else:
            print(f"⚠️ [RLMClient WARNING]: .env file not found at {env_path}")


    async def process(self, user_prompt: str, system_instruction: str = "You are a helpful AI assistant. Respond in JSON format.", preset: str = "medium") -> Dict[str, Any]:
        """
        Sends a prompt to the RLM and returns the parsed JSON response.
        This method should ideally integrate with the LangGraph RLM for advanced reasoning.
        For now, it's a direct call to the GenAI model.
        """
        if not self.client or not self.generation_config:
            return {
                "final_result": "API Key Missing or Client not initialized. Simulated RLM response.",
                "confidence": 0.0,
                "decomposed_tasks": [],
                "cache_hits": 0,
                "retry_count": 0
            }

        try:
            response = None # Initialize response to None
            # Simulate asynchronous call to the GenAI model
            # For actual LangGraph integration, you'd call rlm_langgraph.py's process here.
            # Use a dummy system instruction for the direct GenAI call if not provided
            effective_system_instruction = system_instruction if system_instruction else "You are a helpful AI assistant."

            response = await asyncio.to_thread(self.client.generate_content,
                contents=[effective_system_instruction, user_prompt], # Pass system instruction as part of contents
                generation_config=self.generation_config,
            )

            # Parse the JSON string back into a Python dictionary
            # The model often wraps its JSON in markdown code blocks, try to extract it.
            response_text = response.text.strip()
            if response_text.startswith("```json") and response_text.endswith("```"):
                json_string = response_text[7:-3].strip()
            else:
                json_string = response_text

            parsed_json = json.loads(json_string)

            # Attempt to extract relevant part, e.g., 'root_cause' or 'business_impact'
            # If not found, return the full parsed JSON
            final_result_text = parsed_json.get("root_cause") or \
                                parsed_json.get("business_impact") or \
                                parsed_json.get("prevention_plan") or \
                                json_string # Fallback to full string if no specific field

            return {
                "final_result": final_result_text,
                "confidence": 0.85, # Mock confidence
                "decomposed_tasks": ["Simulated decomposition - direct GenAI call"],
                "cache_hits": 0,
                "retry_count": 0
            }

        except json.JSONDecodeError as e:
            response_text_snippet = response.text[:200] if response else "[No response text available]"
            print(f"❌ [RLMClient ERROR]: JSON decoding failed: {e}. Raw response: {response_text_snippet}")
            return {
                "final_result": f"RLM JSON decoding failure: {e}. Raw: {response_text_snippet}...",
                "confidence": 0.0,
                "decomposed_tasks": [],
                "cache_hits": 0,
                "retry_count": 0
            }
        except Exception as e:
            print(f"❌ [RLMClient ERROR]: An unexpected error occurred during RLM process: {e}")
            return {
                "final_result": f"RLM Failure: {e}",
                "confidence": 0.0,
                "decomposed_tasks": [],
                "cache_hits": 0,
                "retry_count": 0
            }

