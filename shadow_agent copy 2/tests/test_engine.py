"""
Tests for the ShadowTestEngine core logic.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from shadow_agent.core.engine import ShadowTestEngine
from shadow_agent.config.settings import ShadowTestConfig, ShadowMode
from shadow_agent.models.schemas import InferenceRequest, InferenceResponse, RequestStatus

@pytest.fixture
def default_config():
    """Returns a default ShadowTestConfig."""
    return ShadowTestConfig(test_name="engine-test")

def test_engine_initialization(default_config):
    """Tests that the engine and its components are initialized correctly."""
    engine = ShadowTestEngine(default_config)
    assert engine.config.test_name == "engine-test"
    assert engine._running is False
    assert engine.traffic_mirror is not None
    assert engine.model_client is not None
    assert engine.evaluator is not None
    assert engine.storage is not None

@pytest.mark.asyncio
async def test_call_model_success(default_config):
    """Tests the _call_model method on a successful API call."""
    engine = ShadowTestEngine(default_config)
    
    # Mock the model client's call method
    mock_response = InferenceResponse(status=RequestStatus.COMPLETED, content="Success")
    engine.model_client.call = AsyncMock(return_value=mock_response)
    
    request = InferenceRequest(request_id="test-1")
    response = await engine._call_model(default_config.champion, request)
    
    assert response.status == RequestStatus.COMPLETED
    assert response.content == "Success"
    assert response.latency_ms > 0

@pytest.mark.asyncio
async def test_call_model_failure(default_config):
    """Tests the _call_model method on a failed API call."""
    engine = ShadowTestEngine(default_config)
    
    # Mock the model client's call method to raise an exception
    engine.model_client.call = AsyncMock(side_effect=Exception("API Error"))
    
    request = InferenceRequest(request_id="test-2")
    response = await engine._call_model(default_config.champion, request)
    
    assert response.status == RequestStatus.FAILED
    assert response.error == "API Error"
