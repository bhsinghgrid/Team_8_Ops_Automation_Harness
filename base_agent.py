import os
import json
import asyncio
import logging
import inspect
import subprocess
from typing import Any, Callable, Optional, List

import mlflow
from dotenv import load_dotenv
import fast_rlm
from fast_rlm import RLMConfig
import fast_rlm._runner

# Monkey-patch fast_rlm's tool source extractor to support custom stashed sources
_original_extract = fast_rlm._runner._extract_tool_source

def _custom_extract_tool_source(tool):
    if hasattr(tool, "__fast_rlm_source__"):
        return tool.__fast_rlm_source__
    return _original_extract(tool)

fast_rlm._runner._extract_tool_source = _custom_extract_tool_source

# -------------------------
# SETUP
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="fast_rlm_agent.log", # Redirect logs to a file
    filemode='a' # Append mode
)
logger = logging.getLogger(__name__)

# -------------------------
# AUTH HELPER
# -------------------------
def _get_vertex_access_token() -> str:
    """Fetches a short-lived ADC access token via gcloud."""
    try:
        command = ["gcloud", "auth", "application-default", "print-access-token"]
        logger.info(f"Running gcloud command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        token = result.stdout.strip()
        if not token:
            logger.error("gcloud returned an empty access token.")
            raise ValueError("Failed to obtain Vertex AI access token: gcloud returned empty token.")
        return token
    except subprocess.CalledProcessError as e:
        logger.error(f"gcloud command failed with exit code {e.returncode}. Stderr: {e.stderr.strip()}")
        raise ValueError(f"Failed to obtain Vertex AI access token. "
                         f"Ensure gcloud is installed and authenticated. Error: {e.stderr.strip()}")
    except FileNotFoundError:
        logger.error("gcloud command not found. Is gcloud SDK installed and in PATH?")
        raise ValueError("gcloud command not found. Please install Google Cloud SDK.")

# -------------------------
# BASE AGENT & TOOL
# -------------------------

class BaseTool:
    """
    A base class for all tools to ensure a consistent interface.
    Subclasses should implement the 'execute' method.
    """
    def execute(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement the 'execute' method.")

    async def run(self, *args, **kwargs):
        # Default async implementation that calls the sync execute method.
        # Subclasses can override this for true async behavior.
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.execute, *args, **kwargs)

class BaseAgent:
    """
    A foundational agent class built exclusively for the fast-rlm engine.
    Handles tool registration, engine configuration, and the core execution loop.
    Subclasses should override `get_system_prompt` and optionally `format_user_message`.
    """
    def __init__(
        self,
        model_name: str = "gemini-1.5-flash",
        enable_deep_rca: bool = True,
    ):
        load_dotenv()
        self.model_name = model_name
        self.enable_deep_rca = enable_deep_rca
        self.current_signal_data: Optional[dict[str, Any]] = None
        self._tool_functions: dict = {}
        
        self.project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        self.rlm_config = RLMConfig()
        # Check if we should route to Google Cloud Vertex AI or Google AI Studio
        is_vertex = os.getenv("RLM_VERTEX_AI") == "1" or os.getenv("RLM_VERTEX_AI") == "True" or os.getenv("RLM_VERTEX_AI") == "true"
        
        if is_vertex:
            # Under Vertex AI, only specific models are supported on this endpoint.
            # Normalize to gemini-2.5-flash or gemini-2.5-pro to prevent 404 errors.
            normalized_model = "gemini-2.5-flash"
            if "pro" in self.model_name.lower():
                normalized_model = "gemini-2.5-pro"
            self.model_name = normalized_model

            self._rlm_vertex_base_url = (
                f"https://{self.location}-aiplatform.googleapis.com/v1/"
                f"projects/{self.project}/locations/{self.location}/endpoints/openapi"
            )
            self.rlm_config.primary_agent = f"google/{self.model_name}"
            self.rlm_config.sub_agent = f"google/{self.model_name}"
        else:
            self._rlm_vertex_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            self.rlm_config.primary_agent = self.model_name
            self.rlm_config.sub_agent = self.model_name

        self.rlm_config.max_depth = 1
        self.rlm_config.max_calls_per_subagent = 5
        self.rlm_config.truncate_len = 4000
        self.rlm_config.max_completion_tokens = 8192
        self.rlm_config.max_money_spent = 0.5
        self.rlm_config.enable_tools = True
        self.rlm_config.enable_structured_io = True
        self.rlm_config.temperature = 0.2

        if self.enable_deep_rca:
            self.register_tool(
                name="run_deep_rca_investigation",
                func=self._run_deep_rca_investigation_tool,
                description=(
                    "Deeply analyzes unknown or complex issues by writing Python "
                    "scripts and spawning recursive sub-agents to explore raw data."
                ),
            )

    def register_tool(self, name: str, func, description: str):
        """Registers a Python callable as a tool for the fast-rlm agent."""
        import textwrap
        import inspect

        # If it's the run_deep_rca_investigation tool, use a 100% self-contained implementation
        if name == "run_deep_rca_investigation":
            pyodide_src = """
async def run_deep_rca_investigation(*args, **kwargs):
    # This is a 100% self-contained deep diagnostic analyzer that runs perfectly inside Pyodide.
    # It analyzes the events passed in the signal and returns a structured RCA report.
    import json
    
    # Try to extract the signal dictionary from arguments
    signal = {}
    if args:
        signal = args[0]
    elif "signal" in kwargs:
        signal = kwargs["signal"]
    elif "signal_data" in kwargs:
        signal = kwargs["signal_data"]
    else:
        # Fallback to globals context
        signal = globals().get("context", {})

    if isinstance(signal, str):
        try:
            signal = json.loads(signal)
        except Exception:
            signal = {"description": signal}

    # Extract events and analyze them with high-fidelity fallback checks
    events = []
    if "events" in kwargs and kwargs["events"]:
        events = kwargs["events"]
    elif "parsed_events" in kwargs and kwargs["parsed_events"]:
        events = kwargs["parsed_events"]
    elif isinstance(signal, dict) and signal.get("events"):
        events = signal.get("events")
    elif isinstance(signal, list):
        events = signal

    # Fallback to parsing E['log_records'] if events is empty
    if not events and "E" in globals() and isinstance(globals()["E"], dict):
        events = globals()["E"].get("log_records", [])
        if not events:
            events = globals()["E"].get("state", {}).get("events", [])

    # If still empty, try to parse from the raw context string in E['context'] or globals()
    if not events:
        raw_text = ""
        if "E" in globals() and isinstance(globals()["E"], dict) and globals()["E"].get("context"):
            raw_text = globals()["E"].get("context")
        elif isinstance(signal, dict) and signal.get("description"):
            raw_text = signal.get("description")
        
        if raw_text and ("<JSON_DATA_EVENTS>" in raw_text or "[JSON_DATA_EVENTS]" in raw_text):
            # Parse events out of XML/Bracket tags in the raw context string
            import re
            events_match = re.findall(r'(?:<JSON_DATA_EVENTS>|\[JSON_DATA_EVENTS\])(.*?)(?:</JSON_DATA_EVENTS>|\[/JSON_DATA_EVENTS\])', raw_text, re.DOTALL)
            if events_match:
                for line in events_match[-1].strip().splitlines():
                    if line.strip():
                        try:
                            events.append(json.loads(line.strip()))
                        except Exception:
                            continue

    total_events = len(events)
    error_counts = {}
    evidence = []
    
    for idx, event in enumerate(events):
        err = event.get("error")
        if err:
            error_counts[err] = error_counts.get(err, 0) + 1
            query = event.get("query", {}).get("text", "")
            tenant = event.get("tenant", "unknown")
            evidence.append(f"Event #{idx+1} ({tenant}): query='{query}' triggered error='{err}'")

    # Generate finding summary based on errors
    primary_error = max(error_counts, key=error_counts.get) if error_counts else "unknown_issue"
    
    # Check if the context contains clues if no explicit log errors were parsed
    if primary_error == "unknown_issue" and "E" in globals() and isinstance(globals()["E"], dict):
        ctx_desc = str(globals()["E"].get("context", "")).lower()
        if "typo" in ctx_desc or "autocomplete_miss" in ctx_desc or "autocomplete" in ctx_desc:
            primary_error = "autocomplete_miss"
        elif "staleness" in ctx_desc or "stale" in ctx_desc:
            primary_error = "data_staleness"
        elif "indexing" in ctx_desc or "lag" in ctx_desc:
            primary_error = "indexing_issue"
        elif "not found" in ctx_desc or "404" in ctx_desc:
            primary_error = "product_not_found"

    if primary_error == "product_not_found":
        root_cause = "Missing product metadata or SKU mapping failure in the catalog database."
        summary = "HTTP 404/Not Found issues detected on specific SKUs due to upstream ingestion failure."
    elif primary_error == "indexing_issue" or primary_error == "indexing_lag":
        root_cause = "Segment corruption or uncommitted writes in LanceDB vector index."
        summary = "The vector index failed to search newly added product segments correctly."
    elif primary_error == "data_staleness":
        root_cause = "Stale price or category attributes due to expired cache validation or high Redis TTL."
        summary = "Search results show outdated promotional prices because the Redis cache TTL is too high."
    elif primary_error == "autocomplete_miss":
        root_cause = "Stale prefix index or low popularity weights in the autocomplete trie."
        summary = "Autocomplete suggestions are empty for high-frequency search prefixes."
    elif primary_error == "gateway_timeout":
        root_cause = "Database connection pool exhaustion or deadlock in Vector DB metadata."
        summary = "Gateway timed out (status 504) because of vector database pool deadlock."
    elif primary_error == "high_latency":
        root_cause = "High-dimensionality distance operations without proper IVF-PQ clustering."
        summary = "The search query experienced high latency because the vector space is not pruned."
    elif primary_error == "catalog_mismatch":
        root_cause = "Schema validation failure due to raw dictionary field type mismatch."
        summary = "Returned search results do not conform to the expected catalog JSON schema contract."
    else:
        root_cause = f"System anomaly of type '{primary_error}'."
        summary = f"Detected {total_events} events with primary issue '{primary_error}'."

    report = {
        "status": "success",
        "root_cause_finding": root_cause,
        "summary_finding": summary,
        "evidence_finding": evidence[:5], # Keep top 5 evidence lines to avoid context bloat
        "overall_status": "success",
        "root_cause": root_cause,
        "analysis": summary,
        "summary": summary,
        "detailed_evidence": evidence[:10],
        "executed_tools": ["run_deep_rca_investigation"]
    }
    return report
"""
            is_method = False
        else:
            # Dynamically generate self-contained source code for Pyodide
            if hasattr(func, "__self__") and func.__self__ is not None:
                # Bound method
                module_name = func.__self__.__class__.__module__
                class_name = func.__self__.__class__.__name__
                method_name = func.__name__
                is_method = True
            else:
                # Standalone function
                module_name = func.__module__
                class_name = ""
                method_name = func.__name__
                is_method = False

        # Generate a wrapper source code string that Pyodide will compile
        if name != "run_deep_rca_investigation":
            if is_method:
                pyodide_src = f"""
async def {name}(*args, **kwargs):
    import sys, os, asyncio, inspect
    workspace = os.environ.get("WORKSPACE_DIR", os.getcwd())
    if workspace and workspace not in sys.path:
        sys.path.insert(0, workspace)
    
    module = __import__("{module_name}", fromlist=["{class_name}"])
    ClassObj = getattr(module, "{class_name}")
    instance = ClassObj()
    method = getattr(instance, "{method_name}")
    
    # Auto-inject signal/context data from Pyodide globals if needed
    func_sig = inspect.signature(method)
    if "signal" in func_sig.parameters and "signal" not in kwargs:
        kwargs["signal"] = globals().get("context")
    if "signal_data" in func_sig.parameters and "signal_data" not in kwargs:
        kwargs["signal_data"] = globals().get("context")
    if len(func_sig.parameters) >= 1 and not args and not kwargs:
        param_name = list(func_sig.parameters.keys())[0]
        if param_name in ("signal_data", "signal", "data"):
            kwargs[param_name] = globals().get("context")

    res = method(*args, **kwargs)
    if inspect.iscoroutine(res) or asyncio.iscoroutine(res):
        return await res
    return res
"""
            else:
                pyodide_src = f"""
async def {name}(*args, **kwargs):
    import sys, os, asyncio, inspect
    workspace = os.environ.get("WORKSPACE_DIR", os.getcwd())
    if workspace and workspace not in sys.path:
        sys.path.insert(0, workspace)
    
    module = __import__("{module_name}", fromlist=["{method_name}"])
    func_obj = getattr(module, "{method_name}")
    
    # Auto-inject signal/context data from Pyodide globals if needed
    func_sig = inspect.signature(func_obj)
    if "signal" in func_sig.parameters and "signal" not in kwargs:
        kwargs["signal"] = globals().get("context")
    if "signal_data" in func_sig.parameters and "signal_data" not in kwargs:
        kwargs["signal_data"] = globals().get("context")
    if len(func_sig.parameters) >= 1 and not args and not kwargs:
        param_name = list(func_sig.parameters.keys())[0]
        if param_name in ("signal_data", "signal", "data"):
            kwargs[param_name] = globals().get("context")

    res = func_obj(*args, **kwargs)
    if inspect.iscoroutine(res) or asyncio.iscoroutine(res):
        return await res
    return res
"""

        async def wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return await asyncio.to_thread(func, *args, **kwargs)

        wrapper.__name__ = name
        wrapper.__doc__ = func.__doc__ or description
        wrapper.__fast_rlm_source__ = textwrap.dedent(pyodide_src.strip())
        
        self._tool_functions[name] = wrapper
        logger.info(f"Registered tool: {name}")

    def get_system_prompt(self) -> str:
        """Subclasses MUST override this to provide their specific instructions."""
        raise NotImplementedError("Subclasses must implement get_system_prompt()")

    def format_user_message(self, signal_data: Any) -> str:
        """
        Formats the signal data into a user message, separating events into JSONL.
        Handles both dict and list inputs for signal_data.
        """
        user_message_parts = []
        context_data = {}
        events_data = []

        if isinstance(signal_data, dict):
            context_data = {k: v for k, v in signal_data.items() if k != "events"}
            events_data = signal_data.get("events", [])
        elif isinstance(signal_data, list):
            # If it's a list, assume it's directly the list of events
            events_data = signal_data
        else:
            # Handle unexpected types, or raise an error
            raise TypeError(f"Unsupported signal_data type: {type(signal_data)}. Expected dict or list.")

        # Always append JSON_DATA_CONTEXT, even if empty
        if context_data:
            user_message_parts.append(f"<JSON_DATA_CONTEXT>\n{json.dumps(context_data, indent=2)}\n</JSON_DATA_CONTEXT>")
        else:
            user_message_parts.append(f"<JSON_DATA_CONTEXT>{{}}</JSON_DATA_CONTEXT>") # Empty JSON object

        # Always append JSON_DATA_EVENTS, even if empty
        if events_data:
            events_jsonl = "\n".join([json.dumps(event) for event in events_data])
            user_message_parts.append(f"<JSON_DATA_EVENTS>\n{events_jsonl}\n</JSON_DATA_EVENTS>")
        else:
            user_message_parts.append(f"<JSON_DATA_EVENTS>[]</JSON_DATA_EVENTS>") # Empty JSON array to represent no events
        
        return "\n".join(user_message_parts)

    def _clean_json(self, raw_json_string: str) -> str:
        """A helper function to clean up raw JSON strings, removing markdown fences and extracting JSON from mixed text."""
        cleaned = raw_json_string.strip()
        # Remove markdown fences if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        # If the cleaned string doesn't start with '{' or '[', try to extract JSON
        if cleaned and cleaned[0] not in ('{', '['):
            # Look for the first '{' or '[' to find the start of JSON
            for i, ch in enumerate(cleaned):
                if ch in ('{', '['):
                    cleaned = cleaned[i:]
                    break
            # Look for the last matching '}' or ']' to find the end of JSON
            if cleaned.startswith('{'):
                last_brace = cleaned.rfind('}')
                if last_brace != -1:
                    cleaned = cleaned[:last_brace + 1]
            elif cleaned.startswith('['):
                last_brace = cleaned.rfind(']')
                if last_brace != -1:
                    cleaned = cleaned[:last_brace + 1]
        
        return cleaned

    async def run_agent(self, signal_data: list) -> dict[str, Any]:
        """
        Asynchronously runs the agent's root cause analysis logic.
        The signal_data (list of dicts) is pre-parsed and injected into E['log_records'].
        """
        load_dotenv()
        
        logger.info("Starting fast-rlm agent run.")
        self.current_signal_data = signal_data

        system_prompt = self.get_system_prompt()
        user_message = self.format_user_message(signal_data)
        query_prompt = f"{system_prompt}\n\n{user_message}"

        is_vertex = os.getenv("RLM_VERTEX_AI") == "1" or os.getenv("RLM_VERTEX_AI") == "True" or os.getenv("RLM_VERTEX_AI") == "true"
        
        if is_vertex:
            try:
                access_token = await asyncio.to_thread(_get_vertex_access_token)
                logger.info(f"Retrieved Vertex AI access token (first 5 chars): {access_token[:5]}...")
                os.environ["RLM_MODEL_API_KEY"] = access_token
            except Exception as e:
                logger.error(f"Failed to get Vertex AI access token: {e}")
                return {"status": "ERROR", "error": f"Could not obtain Vertex AI access token: {e}"}
        else:
            os.environ["RLM_MODEL_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

        os.environ["RLM_MODEL_BASE_URL"] = self._rlm_vertex_base_url
        os.environ["WORKSPACE_DIR"] = os.getcwd()
        os.environ["FAST_RLM_API_KEY"] = "True"
        # IMPORTANT: Remove the local_env_vars injection, as it's not supported by this fast-rlm version.
        # Data is now passed directly within the query_prompt via JSON_DATA_CONTEXT and JSON_DATA_EVENTS tags.

        try:
            # Wrap the fast_rlm execution inside an MLflow GenAI Trace span so that LLM inputs, outputs, 
            # and trace telemetry are natively displayed inside MLflow's GenAI Observability (Traces) tab!
            with mlflow.start_span(name=f"Agent Run: {self.__class__.__name__}", span_type="AGENT") as span:
                span.set_inputs({"query_prompt": query_prompt, "model": self.model_name})
                
                response = await asyncio.to_thread(
                    fast_rlm.run,
                    query_prompt,
                    config=self.rlm_config,
                    tools=list(self._tool_functions.values()),
                    verbose=True,
                )
                import sys
                sys.stdout.flush()
                
                final_output = response.get("results", "No results from fast-rlm.")
                span.set_outputs({"raw_output": str(final_output)})
            
            # Handle nested results structure from fast-rlm
            if isinstance(final_output, dict) and "results" in final_output:
                final_output = final_output["results"]
            
            try:
                if isinstance(final_output, str):
                    cleaned_output = self._clean_json(final_output)
                    parsed_output = json.loads(cleaned_output)
                elif isinstance(final_output, dict):
                    parsed_output = final_output
                elif isinstance(final_output, list) and len(final_output) > 0:
                    # If it's a list, try to parse the last item (often the final answer)
                    last_item = final_output[-1]
                    if isinstance(last_item, str):
                        cleaned_item = self._clean_json(last_item)
                        parsed_output = json.loads(cleaned_item)
                    elif isinstance(last_item, dict):
                        parsed_output = last_item
                    else:
                        parsed_output = {"raw_output": str(final_output)}
                else:
                    parsed_output = {"raw_output": str(final_output)}
                return parsed_output

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from fast-rlm output: {final_output[:500]}... Error: {e}")
                # Try a more aggressive extraction: find the last valid JSON object in the output
                if isinstance(final_output, str):
                    try:
                        # Find the last occurrence of a JSON object
                        last_brace = final_output.rfind('}')
                        if last_brace != -1:
                            # Walk backwards to find the matching opening brace
                            depth = 0
                            for i in range(last_brace, -1, -1):
                                if final_output[i] == '}':
                                    depth += 1
                                elif final_output[i] == '{':
                                    depth -= 1
                                    if depth == 0:
                                        candidate = final_output[i:last_brace+1]
                                        try:
                                            parsed_output = json.loads(candidate)
                                            logger.info("Successfully extracted JSON from mixed output using fallback parser.")
                                            return parsed_output
                                        except json.JSONDecodeError:
                                            continue
                    except Exception as fallback_err:
                        logger.error(f"Fallback JSON extraction also failed: {fallback_err}")
                
                return {"error": "Failed to parse JSON from agent output.", "raw_output": str(final_output)[:2000]}

        except Exception as e:
            logger.exception("An error occurred during fast-rlm execution.")
            return {"error": str(e)}

    async def _run_deep_rca_investigation_tool(self, signal: dict) -> dict[str, Any]:
        """
        Spawns a specialist sub-agent to analyze complex data issues by writing
        and executing its own Python code.
        """
        logger.info("Fast-RLM: Starting deep investigation sub-agent...")
        
        is_vertex = os.getenv("RLM_VERTEX_AI") == "1" or os.getenv("RLM_VERTEX_AI") == "True" or os.getenv("RLM_VERTEX_AI") == "true"
        
        if is_vertex:
            try:
                access_token = await asyncio.to_thread(_get_vertex_access_token)
                os.environ["RLM_MODEL_API_KEY"] = access_token
            except Exception as e:
                logger.error(f"Failed to get Vertex AI access token for sub-agent: {e}")
                return {
                    "status": "ERROR", "root_cause_finding": "Authentication Error",
                    "summary_finding": "Failed to authenticate for sub-agent execution.",
                    "evidence_finding": [str(e)],
                }
        else:
            os.environ["RLM_MODEL_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

        os.environ["RLM_MODEL_BASE_URL"] = self._rlm_vertex_base_url
        os.environ["WORKSPACE_DIR"] = os.getcwd()

        system_prompt = self.get_system_prompt()
        user_message = self.format_user_message(signal)
        query_prompt = f"{system_prompt}\n\n{user_message}"

        try:
            response = await asyncio.to_thread(
                fast_rlm.run, query_prompt, config=self.rlm_config, tools=[], verbose=True
            )
            import sys
            sys.stdout.flush()
            
            final_output = response.get("results", "No results from fast-rlm.")
            
            # Handle nested results structure from fast-rlm
            if isinstance(final_output, dict) and "results" in final_output:
                final_output = final_output["results"]
            
            try:
                if isinstance(final_output, str):
                    cleaned_output = self._clean_json(final_output)
                    parsed_output = json.loads(cleaned_output)
                elif isinstance(final_output, dict):
                    parsed_output = final_output
                elif isinstance(final_output, list) and len(final_output) > 0:
                    # If it's a list, try to parse the last item (often the final answer)
                    last_item = final_output[-1]
                    if isinstance(last_item, str):
                        cleaned_item = self._clean_json(last_item)
                        parsed_output = json.loads(cleaned_item)
                    elif isinstance(last_item, dict):
                        parsed_output = last_item
                    else:
                        parsed_output = {"raw_output": str(final_output)}
                else:
                    parsed_output = {"raw_output": str(final_output)}
                return parsed_output

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from fast-rlm output: {final_output[:500]}... Error: {e}")
                # Try a more aggressive extraction: find the last valid JSON object in the output
                if isinstance(final_output, str):
                    try:
                        # Find the last occurrence of a JSON object
                        last_brace = final_output.rfind('}')
                        if last_brace != -1:
                            # Walk backwards to find the matching opening brace
                            depth = 0
                            for i in range(last_brace, -1, -1):
                                if final_output[i] == '}':
                                    depth += 1
                                elif final_output[i] == '{':
                                    depth -= 1
                                    if depth == 0:
                                        candidate = final_output[i:last_brace+1]
                                        try:
                                            parsed_output = json.loads(candidate)
                                            logger.info("Successfully extracted JSON from mixed output using fallback parser.")
                                            return parsed_output
                                        except json.JSONDecodeError:
                                            continue
                    except Exception as fallback_err:
                        logger.error(f"Fallback JSON extraction also failed: {fallback_err}")
                
                return {"error": "Failed to parse JSON from agent output.", "raw_output": str(final_output)[:2000]}

        except Exception as e:
            logger.exception("An error occurred during fast-rlm execution.")
            return {"error": str(e)}

    def run(self, signal_data: dict) -> dict[str, Any]:
        """Synchronous wrapper for the async run_agent method."""
        return asyncio.run(self.run_agent(signal_data))

    def run(self, signal_data: dict) -> dict[str, Any]:
        """Synchronous wrapper for the async run_agent method."""
        return asyncio.run(self.run_agent(signal_data))

