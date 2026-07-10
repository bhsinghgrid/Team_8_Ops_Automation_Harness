"""
Shadow Agent — a LangChain agent for managing and interacting with the shadow testing engine.
"""
import asyncio
import logging
from typing import Type, Dict, Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from shadow_agent.core.engine import ShadowTestEngine
from shadow_agent.config.settings import ShadowTestConfig
from shadow_agent.models.schemas import InferenceRequest

logger = logging.getLogger(__name__)


# --- Tool Inputs ---

class StartShadowTestInput(BaseModel):
    """Input for starting the shadow test engine."""
    config: Dict[str, Any] = Field(description="Shadow test configuration as a dictionary")

class ProcessRequestInput(BaseModel):
    """Input for processing a single inference request."""
    request_id: str = Field(description="Unique ID for the request")
    messages: list[dict] = Field(description="List of messages for the model")

class GetSummaryInput(BaseModel):
    """Input for getting the shadow test results summary."""
    pass

class StopShadowTestInput(BaseModel):
    """Input for stopping the shadow test engine."""
    pass


# --- Tools ---

class StartShadowTestTool(BaseTool):
    """Tool to start the shadow test engine."""
    name: str = "start_shadow_test"
    description: str = "Starts the shadow test engine with a given configuration."
    args_schema: Type[BaseModel] = StartShadowTestInput
    engine: ShadowTestEngine

    def _run(self, config: Dict[str, Any]) -> str:
        """Use this to start the shadow test."""
        try:
            shadow_config = ShadowTestConfig(**config)
            self.engine = ShadowTestEngine(shadow_config)
            asyncio.run(self.engine.start())
            return "Shadow test engine started successfully."
        except Exception as e:
            return f"Error starting engine: {e}"

class ProcessRequestTool(BaseTool):
    """Tool to process a single inference request."""
    name: str = "process_request"
    description: str = "Processes a single inference request through the shadow test engine."
    args_schema: Type[BaseModel] = ProcessRequestInput
    engine: ShadowTestEngine

    def _run(self, request_id: str, messages: list[dict]) -> str:
        """Use this to process a request."""
        if not self.engine or not self.engine._running:
            return "Error: Shadow test engine is not running. Please start it first."
        
        try:
            request = InferenceRequest(
                request_id=request_id,
                messages=messages
            )
            response = asyncio.run(self.engine.process_request(request))
            return f"Request processed. Champion response: {response.content}"
        except Exception as e:
            return f"Error processing request: {e}"

class GetSummaryTool(BaseTool):
    """Tool to get the results summary."""
    name: str = "get_summary"
    description: str = "Gets the aggregated results summary of the shadow test."
    args_schema: Type[BaseModel] = GetSummaryInput
    engine: ShadowTestEngine

    def _run(self) -> str:
        """Use this to get the summary."""
        if not self.engine:
            return "Error: Shadow test engine is not running."
        
        try:
            summary = asyncio.run(self.engine.get_results_summary())
            import json
            import dataclasses
            return json.dumps(dataclasses.asdict(summary), indent=2)
        except Exception as e:
            return f"Error getting summary: {e}"

class StopShadowTestTool(BaseTool):
    """Tool to stop the shadow test engine."""
    name: str = "stop_shadow_test"
    description: str = "Stops the shadow test engine."
    args_schema: Type[BaseModel] = StopShadowTestInput
    engine: ShadowTestEngine

    def _run(self) -> str:
        """Use this to stop the engine."""
        if not self.engine or not self.engine._running:
            return "Engine is not running."
        
        try:
            asyncio.run(self.engine.stop())
            return "Shadow test engine stopped successfully."
        except Exception as e:
            return f"Error stopping engine: {e}"


def create_shadow_agent(config: ShadowTestConfig, llm: ChatOpenAI):
    """Creates a LangChain agent with tools to control the ShadowTestEngine."""
    
    engine = ShadowTestEngine(config)
    
    tools = [
        StartShadowTestTool(engine=engine),
        ProcessRequestTool(engine=engine),
        GetSummaryTool(engine=engine),
        StopShadowTestTool(engine=engine),
    ]

    # Create the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful shadow testing agent. You can start, stop, process requests, and get summaries of shadow tests. Use the available tools to fulfill requests."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # This is a simplified way to create an agent with the modern API.
    # A more robust solution would involve creating a custom graph with LangGraph.
    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: x["intermediate_steps"],
            "chat_history": lambda x: x["chat_history"],
        }
        | prompt
        | llm
    )
    
    # The executor is now the agent itself
    return agent
