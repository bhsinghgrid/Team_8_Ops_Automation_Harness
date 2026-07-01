import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file
from shadow_agent.config.settings import ShadowTestConfig, JudgeConfig, GatingRule, MLflowConfig, ModelConfig, GatingAction
from shadow_agent.core.engine import ShadowTestEngine
from shadow_agent.models.schemas import InferenceRequest, EvaluationResult, InferenceResponse, RequestStatus

logger = logging.getLogger(__name__)

class ShadowEvaluationHarness:
    """
    A dedicated harness for running shadow tests and evaluating champion vs challenger models.
    Integrates with the ShadowTestEngine to perform comprehensive evaluations and apply gating rules.
    """

    def __init__(self, config: ShadowTestConfig):
        self.config = config
        self.shadow_test_engine = ShadowTestEngine(config)
        self.evaluations: List[EvaluationResult] = []

    async def run_shadow_evaluation(self, requests: List[InferenceRequest]) -> List[EvaluationResult]:
        """
        Runs a series of shadow tests for the given inference requests.

        Args:
            requests: A list of InferenceRequest objects to be processed.

        Returns:
            A list of EvaluationResult objects from each processed request.
        """
        logger.info(f"Starting shadow evaluation for {len(requests)} requests...")
        await self.shadow_test_engine.start()
        
        for i, request in enumerate(requests):
            logger.debug(f"Processing request {i+1}/{len(requests)}: {request.request_id}")
            try:
                # The process_request method handles running champion/challenger,
                # evaluation, logging, metrics, and gating internally.
                # It returns the EvaluationResult which we store.
                await self.shadow_test_engine.process_request(request)
                # Note: The actual EvaluationResult is stored by the engine's storage component.
                # We can fetch a summary or individual results later if needed,
                # or rely on the engine's internal buffering and reporting.
            except Exception as e:
                logger.error(f"Error processing request {request.request_id}: {e}", exc_info=True)
                # Optionally, create a minimal error evaluation result if the engine itself fails
                self.evaluations.append(
                    EvaluationResult(
                        request_id=request.request_id,
                        verdict=EvaluationVerdict.ERROR,
                        overall_score=0.0,
                        metadata={"error": str(e)},
                        champion_latency_ms=0,
                        challenger_latency_ms=0,
                        latency_delta_ms=0,
                        champion_tokens=0,
                        challenger_tokens=0,
                        token_delta=0,
                        judge_scores={}
                    )
                )
        
        # After all requests are processed, the engine will have buffered results and
        # performed gating checks periodically. We can now fetch a summary.
        self.evaluations = await self.shadow_test_engine.storage.get_all_evaluations(self.config.test_name)
        
        logger.info("Shadow evaluation completed.")
        await self.shadow_test_engine.stop()
        return self.evaluations

    async def generate_shadow_report(self) -> Dict[str, Any]:
        """
        Generates a summary report of the shadow evaluation.

        Returns:
            A dictionary containing the summary of the evaluation results.
        """
        logger.info("Generating shadow evaluation report...")
        
        summary = await self.shadow_test_engine.get_results_summary()
        dimension_breakdown = await self.shadow_test_engine.get_dimension_breakdown()

        report = {
            "test_name": self.config.test_name,
            "total_requests": summary.total_requests,
            "overall_pass_rate": summary.pass_rate,
            "avg_overall_score": summary.challenger_avg_score,
            "avg_champion_latency_ms": summary.champion_avg_latency_ms,
            "avg_challenger_latency_ms": summary.challenger_avg_latency_ms,
            "avg_latency_delta_ms": summary.latency_delta_ms,
            "pass_rate": summary.pass_rate,
            "fail_rate": summary.fail_rate,
            "error_rate": summary.error_rate,
            "gating_results": [r.model_dump() for r in summary.gating_results], # Assuming gating results are part of summary
            "dimension_breakdown": dimension_breakdown,
        }
        
        logger.info("Shadow evaluation report generated.")
        return report

# Example Usage (for demonstration, would typically be in a separate script or main function)
async def main():
    # Placeholder for a real ShadowConfig
    # In a real scenario, this would be loaded from a config file or built dynamically


    # Mock Models (replace with actual model loading/clients)
    class MockModelClient:
        async def invoke(self, messages: List[Dict]) -> InferenceResponse:
            import asyncio
            import random
            await asyncio.sleep(random.uniform(0.1, 0.5)) # Simulate latency
            content = f"Mock response for: {messages[-1]['content']}"
            return InferenceResponse(
                model_name="mock-model",
                content=content,
                latency_ms=random.randint(100, 500),
                usage={"total_tokens": len(content.split())}
            )

    champion_client = MockModelClient()
    challenger_client = MockModelClient()

    config = ShadowTestConfig(
        test_name="my_first_shadow_test",
        champion=ModelConfig(
            name="Champion Model",
            provider="gemini",
            model_id="gemini-pro",
            api_key_env="GEMINI_API_KEY"
        ),
        challengers=[
            ModelConfig(
                name="Challenger Model",
                provider="gemini",
                model_id="gemini-pro",
                api_key_env="GEMINI_API_KEY"
            )
        ],
        judge=JudgeConfig(
            provider="gemini", # Assuming Gemini is configured
            model_id="gemini-pro",
            gemini_api_key_env="GEMINI_API_KEY", # Replace with actual API key or env var
            dimensions=["accuracy", "relevance"],
            score_range=(1, 5),
            pass_threshold=3.0,
        ),

        gating_rules=[
            GatingRule(
                name="challenger_score_drop",
                metric="avg_overall_score",
                operator="<",
                threshold=0.95, # Challenger's average score should not drop by more than 5% relative to champion
                window_size=5,
                action=GatingAction.ALERT.value
            ),
            GatingRule(
                name="challenger_latency_increase",
                metric="avg_latency_delta_ms",
                operator=">",
                threshold=500, # Challenger should not be more than 500ms slower on average
                window_size=5,
                action=GatingAction.ALERT.value
            )
        ],
        enable_human_review_queue=False,
        human_review_sample_rate=0.1,
        mlflow=MLflowConfig(
            tracking_uri="http://localhost:5000",
            experiment_name="shadow_testing"
        ),

    )

    harness = ShadowEvaluationHarness(config)

    # Sample Inference Requests
    sample_requests = [
        InferenceRequest(
            request_id="req_1",
            messages=[{"role": "user", "content": "What is the capital of France?"}],
            metadata={"user_id": "user1"}
        ),
        InferenceRequest(
            request_id="req_2",
            messages=[{"role": "user", "content": "Tell me about large language models."}],
            metadata={"user_id": "user2"}
        ),
         InferenceRequest(
            request_id="req_3",
            messages=[{"role": "user", "content": "How does photosynthesis work?"}],
            metadata={"user_id": "user3"}
        ),
         InferenceRequest(
            request_id="req_4",
            messages=[{"role": "user", "content": "Recommend a good sci-fi book."}],
            metadata={"user_id": "user4"}
        ),
         InferenceRequest(
            request_id="req_5",
            messages=[{"role": "user", "content": "Explain quantum computing simply."}],
            metadata={"user_id": "user5"}
        ),
    ]

    await harness.run_shadow_evaluation(sample_requests)
    report = await harness.generate_shadow_report()
    
    import json
    print("--- Shadow Evaluation Report ---")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    import asyncio
    # For a real application, configure logging appropriately
    logging.basicConfig(level=logging.INFO) 
    asyncio.run(main())
