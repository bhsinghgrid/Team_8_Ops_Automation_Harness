"""
LLM-as-Judge — uses an LLM to evaluate and score model outputs.
"""

import logging
from typing import Dict, Optional, Any, List, Literal
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import SystemMessage, HumanMessage

from shadow_agent_framework.config.settings import JudgeConfig
from shadow_agent_framework.models.schemas import (
    InferenceRequest,
    InferenceResponse,
    EvaluationResult,
    JudgeScore,
    EvaluationVerdict,
    RequestStatus,
)

logger = logging.getLogger(__name__)

DEFAULT_JUDGE_PROMPT = """You are an expert LLM evaluator. You will be given:
1. The original user request
2. The champion (production) model's response
3. The challenger (candidate) model's response

Evaluate the challenger's response compared to the champion's on each dimension below.
For each dimension, provide:
- A score from {min_score} to {max_score}
- A brief reasoning
- Whether it passes (score >= {pass_threshold})

Dimensions to evaluate:
{dimensions}

{format_instructions}
"""


# --- Pydantic Models for Structured Output ---

class ScoreModel(BaseModel):
    """Pydantic model for a single dimension's score."""
    score: float = Field(description="The score from {min_score} to {max_score}")
    reasoning: str = Field(description="Brief reasoning for the score")
    passed: bool = Field(description="Whether the score is >= {pass_threshold}")

class JudgeOutputModel(BaseModel):
    """Pydantic model for the complete judge output."""
    scores: Dict[str, ScoreModel] = Field(description="Dictionary of scores per dimension")
    overall_verdict: Literal["pass", "fail", "neutral"] = Field(description="The overall verdict")
    overall_reasoning: str = Field(description="A brief summary of the overall reasoning")


class LLMJudge:
    """
    LLM-as-Judge evaluator.
    
    Uses a separate LLM to compare champion vs challenger responses
    across configurable dimensions (accuracy, relevance, etc.).
    """

    def __init__(self, config: JudgeConfig):
        self.config = config
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
        """Lazy-initialize the judge LLM client."""
        if self._client is None:
            provider = self.config.provider
            api_key = self.config.api_key

            if provider == "openai":
                from langchain_openai import ChatOpenAI
                self._client = ChatOpenAI(
                    model=self.config.model_id,
                    temperature=self.config.temperature,
                    openai_api_key=api_key,
                    request_timeout=60.0,
                )
            elif provider == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                self._client = ChatGoogleGenerativeAI(
                    model=self.config.model_id,
                    temperature=self.config.temperature,
                    google_api_key=api_key,
                    convert_system_message_to_human=True
                )
            elif provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                self._client = ChatAnthropic(
                    model=self.config.model_id,
                    temperature=self.config.temperature,
                    anthropic_api_key=api_key,
                    timeout=60.0,
                )
            else:
                raise ValueError(f"Unsupported judge provider: {provider}")

        return self._client

    async def evaluate(
        self,
        request: InferenceRequest,
        champion_response: InferenceResponse,
        challenger_response: InferenceResponse,
    ) -> EvaluationResult:
        """
        Evaluate a challenger response against the champion using LLM-as-Judge.
        """
        # Skip if either response failed
        if champion_response.status == RequestStatus.FAILED:
            return self._error_result(request.request_id, "Champion response failed")
        if challenger_response.status == RequestStatus.FAILED:
            return self._error_result(request.request_id, "Challenger response failed")

        try:
            client = self._get_client()
            parser = PydanticOutputParser(pydantic_object=JudgeOutputModel)

            # Build the evaluation prompt
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content=DEFAULT_JUDGE_PROMPT),
                HumanMessage(content="""## Original Request
{request_messages}

## Champion Response ({champion_model})
{champion_content}

## Challenger Response ({challenger_model})
{challenger_content}""")
            ])
            
            chain = prompt_template | client | parser

            parsed_result = await chain.ainvoke({
                "min_score": self.config.score_range[0],
                "max_score": self.config.score_range[1],
                "pass_threshold": self.config.pass_threshold,
                "dimensions": "\\n".join(f"- {d}" for d in self.config.dimensions),
                "format_instructions": parser.get_format_instructions(),
                "request_messages": self._format_messages(request.messages),
                "champion_model": champion_response.model_name,
                "champion_content": champion_response.content,
                "challenger_model": challenger_response.model_name,
                "challenger_content": challenger_response.content,
            })

            # Build JudgeScore objects from parsed Pydantic model
            judge_scores: Dict[str, JudgeScore] = {
                dim: JudgeScore(
                    dimension=dim,
                    score=score_data.score,
                    reasoning=score_data.reasoning,
                    passed=score_data.passed
                ) for dim, score_data in parsed_result.scores.items()
            }

            # Calculate overall score
            overall_score = sum(s.score for s in judge_scores.values()) / len(judge_scores) if judge_scores else 0.0

            # Determine verdict
            verdict_map = {
                "pass": EvaluationVerdict.PASS,
                "fail": EvaluationVerdict.FAIL,
                "neutral": EvaluationVerdict.NEUTRAL,
            }
            verdict = verdict_map.get(parsed_result.overall_verdict, EvaluationVerdict.NEUTRAL)

            return EvaluationResult(
                request_id=request.request_id,
                champion_response=champion_response,
                challenger_response=challenger_response,
                judge_scores=judge_scores,
                overall_score=overall_score,
                verdict=verdict,
                champion_latency_ms=champion_response.latency_ms,
                challenger_latency_ms=challenger_response.latency_ms,
                latency_delta_ms=challenger_response.latency_ms - champion_response.latency_ms,
                champion_tokens=champion_response.usage.get("total_tokens", 0),
                challenger_tokens=challenger_response.usage.get("total_tokens", 0),
                token_delta=(
                    challenger_response.usage.get("total_tokens", 0)
                    - champion_response.usage.get("total_tokens", 0)
                ),
                metadata={"overall_reasoning": parsed_result.overall_reasoning},
            )

        except Exception as e:
            logger.error(f"Judge evaluation failed: {e}", exc_info=True)
            return self._error_result(request.request_id, str(e))

    def _parse_judge_response(self, text: str) -> dict:
        """Parse the JSON response from the judge LLM."""
        import json
        import re

        # Try to extract JSON from the response
        # Handle markdown code blocks
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse judge response as JSON: {text[:200]}")
            return {"scores": {}, "overall_verdict": "neutral", "overall_reasoning": "Parse error"}

    def _format_messages(self, messages: list) -> str:
        """Format messages for the judge prompt."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"[{role}]: {content}")
        return "\n".join(formatted)

    def _error_result(self, request_id: str, error: str) -> EvaluationResult:
        """Create an error evaluation result."""
        return EvaluationResult(
            request_id=request_id,
            verdict=EvaluationVerdict.ERROR,
            overall_score=0.0,
            judge_scores={},
            latency_delta_ms=0.0,
            token_delta=0,
            metadata={"error": error},
        )
        return EvaluationResult(
            request_id=request_id,
            verdict=EvaluationVerdict.ERROR,
            overall_score=0.0,
            judge_scores={},
            latency_delta_ms=0.0,
            token_delta=0,
            metadata={"error": error},
        )
        return EvaluationResult(
            request_id=request_id,
            verdict=EvaluationVerdict.ERROR,
            overall_score=0.0,
            judge_scores={},
            latency_delta_ms=0.0,
            token_delta=0,
            metadata={"error": error},
        )
        return EvaluationResult(
            request_id=request_id,
            verdict=EvaluationVerdict.ERROR,
            metadata={"error": error},
        )
