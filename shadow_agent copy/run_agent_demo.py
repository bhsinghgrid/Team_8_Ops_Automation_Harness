"""
Demonstrates running the Shadow Test Agent directly.
"""
import os
import sys
import asyncio
import logging
from uuid import uuid4
from dotenv import load_dotenv # Import load_dotenv
from unittest.mock import patch # Import patch

sys.path.insert(0, 'src')

from shadow_agent.core.engine import ShadowTestEngine
from shadow_agent.config.settings import ShadowTestConfig, ModelConfig, JudgeConfig, RanxConfig, EvaluationStrategy, MLflowConfig
from shadow_agent.models.schemas import InferenceRequest, InferenceResponse, RequestStatus
from shadow_agent.utils.logging_config import setup_logging
import json
import dataclasses

setup_logging()
logger = logging.getLogger(__name__)

async def run_demo():
    load_dotenv() # Load environment variables from .env
    logger.info("Starting Shadow Agent Demo...")

    # --- Configuration for LLM Judge --- 
    # Ensure GEMINI_API_KEY is set in your environment
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable not set. Please set it to run the demo.")
        return

    llm_config = ShadowTestConfig(
        test_name="llm-judge-demo",
        evaluation_strategy=EvaluationStrategy.LLM_JUDGE,
        champion=ModelConfig(
            name="champion-llm", 
            provider="gemini", 
            model_id="gemini-2.5-pro",
            api_key_env=None,
            gemini_api_key_env="GEMINI_API_KEY"
        ),
        challengers=[
            ModelConfig(
                name="challenger-llm",
                provider="gemini",
                model_id="gemini-2.5-pro",
                api_key_env=None,
                gemini_api_key_env="GEMINI_API_KEY"
            )
        ],
        judge=JudgeConfig(
            provider="gemini",
            model_id="gemini-2.5-pro",
            api_key_env=None,
            gemini_api_key_env="GEMINI_API_KEY"
        ),
        mlflow=MLflowConfig(tracking_uri="sqlite:///./mlruns/llm_judge_demo.db", experiment_name="llm-judge-demo-exp")
    )

    # --- Run LLM Judge Demo ---
    logger.info("Running LLM Judge Shadow Test Demo...")
    llm_engine = ShadowTestEngine(llm_config)
    await llm_engine.start()

    requests_to_process = [
        ("What is the capital of France?", "Paris"),
        ("Explain quantum entanglement simply.", "It's a phenomenon where two particles are linked and affect each other instantaneously, regardless of distance."),
        ("Write a short poem about a cat.", "Soft purr and gentle paw, a furry friend beyond compare.")
    ]

    for i, (prompt, expected_response) in enumerate(requests_to_process):
        request_id = str(uuid4())
        messages = [{"role": "user", "content": prompt}]
        logger.info(f"Processing LLM Judge request {i+1}: {prompt[:50]}...")
        await llm_engine.process_request(InferenceRequest(request_id=request_id, messages=messages, metadata={"expected_response": expected_response}))
        await asyncio.sleep(1) # Simulate some delay

    llm_summary = await llm_engine.get_results_summary()
    logger.info({"event": "llm_judge_summary", "summary": dataclasses.asdict(llm_summary)}, extra={"json_fields": True})
    await llm_engine.stop()


    # --- Configuration for RANX Evaluator --- 
    # For RANX, we'll assume product data as content.
    # No API key needed for RANX itself, but challenger/champion still use it

    ranx_config = ShadowTestConfig(
        test_name="ranx-demo",
        evaluation_strategy=EvaluationStrategy.RANX,
        champion=ModelConfig(
            name="champion-ranx", 
            provider="gemini", 
            model_id="gemini-2.5-pro",
            api_key_env=None,
            gemini_api_key_env="GEMINI_API_KEY"
        ),
        challengers=[
            ModelConfig(
                name="challenger-ranx",
                provider="gemini",
                model_id="gemini-2.5-pro",
                api_key_env=None,
                gemini_api_key_env="GEMINI_API_KEY"
            )
        ],
        ranx_config=RanxConfig(metrics=["ndcg@3", "recall@3"]),
        mlflow=MLflowConfig(tracking_uri="sqlite:///./mlruns/ranx_demo.db", experiment_name="ranx-demo-exp")
    )

    # --- Run RANX Demo ---
    logger.info("\nRunning RANX Shadow Test Demo...")
    ranx_engine = ShadowTestEngine(ranx_config)
    await ranx_engine.start()

    # Simulate e-commerce search results
    # The content here would typically come from your LLM responses
    ranx_requests_to_process = [
        {
            "request_id": str(uuid4()),
            "query": "best smartphones",
            "champion_results": [
                {"id": "samsung-s24", "relevance": 3}, 
                {"id": "iphone-16", "relevance": 2}, 
                {"id": "google-pixel-9", "relevance": 1}
            ],
            "challenger_results": [
                {"id": "iphone-16", "score": 0.9}, 
                {"id": "samsung-s24", "score": 0.8}, 
                {"id": "oneplus-12", "score": 0.7}
            ]
        },
        {
            "request_id": str(uuid4()),
            "query": "affordable laptops",
            "champion_results": [
                {"id": "lenovo-ideapad", "relevance": 2},
                {"id": "hp-pavilion", "relevance": 1},
                {"id": "acer-aspire", "relevance": 1}
            ],
            "challenger_results": [
                {"id": "hp-pavilion", "score": 0.9},
                {"id": "lenovo-ideapad", "score": 0.8},
                {"id": "dell-inspiron", "score": 0.6}
            ]
        }
    ]

    for i, req_data in enumerate(ranx_requests_to_process):
        request_id = req_data["request_id"]
        query = req_data["query"]
        champion_content = req_data["champion_results"]
        challenger_content = req_data["challenger_results"]
        
        # Create mock responses for RANX evaluation
        mock_champion_response = InferenceResponse(
            request_id=request_id,
            model_name=ranx_config.champion.name,
            model_id=ranx_config.champion.model_id,
            content=champion_content,
            status=RequestStatus.COMPLETED,
            latency_ms=80.0
        )
        mock_challenger_response = InferenceResponse(
            request_id=request_id,
            model_name=ranx_config.challengers[0].name,
            model_id=ranx_config.challengers[0].model_id,
            content=challenger_content,
            status=RequestStatus.COMPLETED,
            latency_ms=100.0
        )

        # Patch _call_model to return our mock responses for this demo
        with (
            patch('shadow_agent.router.model_client.ModelClient.call', side_effect=[mock_champion_response, mock_challenger_response])
        ):
            # Directly call _run_shadow_pipeline as it handles evaluation
            # For a real scenario, process_request would use the actual LLM calls
            logger.info(f"Processing RANX demo request {i+1}: {query}...")
            await ranx_engine._run_shadow_pipeline(
                request=InferenceRequest(request_id=request_id, messages=[{"role": "user", "content": query}]),
                champion_response=mock_champion_response,
            )
        await asyncio.sleep(1) # Simulate some delay

    ranx_summary = await ranx_engine.get_results_summary()
    logger.info({"event": "ranx_summary", "summary": dataclasses.asdict(ranx_summary)}, extra={"json_fields": True})
    await ranx_engine.stop()
    logger.info("Shadow Agent Demo Finished.")

if __name__ == "__main__":
    asyncio.run(run_demo())
