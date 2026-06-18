import asyncio
import sys
import contextlib
from temporalio import activity

# To ensure the parent directory is in the Python path for module resolution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from temporal.shared import HeartbeatingStream
from Catalog.RootCause.google_agent import GoogleRootCauseAgent
from Catalog.Fix_Proposal.fix_agent import GoogleFixProposalAgent
from Catalog.Eval.eval_agent import GoogleEvalAgent
from Autocomplete.RootCause.main_agent import AutocompleteRootCauseAgent
from Autocomplete.Fix_Proposal.fix_agent import AutocompleteFixProposalAgent
from Autocomplete.Eval.eval_agent import AutocompleteEvalAgent
from Release.release_agent import ReleaseAgent
from Semantic.RootCause.main_agent import SemanticRootCauseAgent
from Semantic.Fix_Proposal.fix_agent import SemanticFixProposalAgent
from Semantic.Eval.eval_agent import SemanticEvalAgent
from Catalog.Eval.Tools.diffy_client import DiffyApiClient # Ensure correct DiffyApiClient is imported
from Catalog.Eval.Tools.diffy_client import DiffyApiClient # Ensure correct DiffyApiClient is imported

@activity.defn
async def root_cause_activity(signal: dict) -> dict:
    """Temporal activity to run the Root Cause Analysis agent."""
    activity.logger.info("Executing Root Cause Analysis activity...")
    agent = GoogleRootCauseAgent()
    
    with HeartbeatingStream() as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            result = await agent.run_agent(signal)
            activity.logger.info("Root Cause Analysis completed.")
            return result

@activity.defn
async def fix_proposal_activity(rca_output: dict) -> dict:
    """
    Runs the Fix Proposal agent, ensures a project exists in Diffy,
    and then creates a new diff in the live Diffy service.
    """
    activity.logger.info("Executing Fix Proposal activity...")
    agent = GoogleFixProposalAgent()
    # Note: The 'apiKey' is the default required by the open-source Diffy project.
    diffy_client = DiffyApiClient(base_url="http://localhost:8888", api_key="apiKey")
    project_slug = "my-ai-project"

    with HeartbeatingStream() as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            fix_result = await agent.run_agent(rca_output)
            activity.logger.info("Fix Proposal completed.")

            # Step 1: Ensure the project exists in Diffy.
            await diffy_client.create_project_if_not_exists(slug=project_slug, name="My AI-Managed Project")

            # Step 2: Create a diff with simulated production and shadow HTTP requests.
            baseline_request = (
                "GET /search?q=shoes HTTP/1.1\n"
                "Host: production.example.com\n"
                "User-Agent: Diffy-Client\n\n"
            )
            shadow_request = (
                "GET /search?q=shoes HTTP/1.1\n"
                "Host: shadow.example.com\n"
                "User-Agent: Diffy-Client\n\n"
            )
            
            activity.logger.info(f"Creating a new diff in project '{project_slug}' on the live Diffy server...")
            diff_creation_result = await diffy_client.create_diff(
                baseline=baseline_request, 
                shadow=shadow_request,
                project=project_slug
            )
            
            return {
                "fix_proposal_summary": fix_result.get("summary", "N/A"),
                "diff_id": diff_creation_result.get("id")
            }


@activity.defn
async def eval_activity(fix_output: dict) -> dict:
    """
    Temporal activity to run the Evaluation agent.
    It receives the output from the fix_proposal_activity, including the
    dynamic 'diff_id', and uses it to run the evaluation.
    """
    activity.logger.info("Executing Evaluation activity...")
    agent = GoogleEvalAgent()

    with HeartbeatingStream() as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            # The signal for the eval agent is now dynamically constructed
            # from the output of the previous activity.
            eval_signal = {
                "diff_id": fix_output.get("diff_id"),
                "context": fix_output.get("fix_proposal_summary")
            }
            result = await agent.run_agent(eval_signal)
            activity.logger.info("Evaluation completed.")
            return result

@activity.defn
async def autocomplete_root_cause_activity(signal: dict) -> dict:
    """Temporal activity to run the Autocomplete Root Cause Analysis agent."""
    activity.logger.info("Executing Autocomplete Root Cause Analysis activity...")
    agent = AutocompleteRootCauseAgent()
    with HeartbeatingStream() as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            return await agent.run_agent(signal)

@activity.defn
async def autocomplete_fix_proposal_activity(rca_output: dict) -> dict:
    """Temporal activity to run the Autocomplete Fix Proposal agent."""
    activity.logger.info("Executing Autocomplete Fix Proposal activity...")
    agent = AutocompleteFixProposalAgent()
    with HeartbeatingStream() as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            return await agent.run_agent(rca_output)

@activity.defn
async def autocomplete_eval_activity(fix_output: dict) -> dict:
    """Temporal activity to run the Autocomplete Evaluation agent."""
    activity.logger.info("Executing Autocomplete Evaluation activity...")
    agent = AutocompleteEvalAgent()
    with HeartbeatingStream() as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            return await agent.run_agent(fix_output)

@activity.defn
async def release_activity(eval_output: dict) -> dict:
    """Temporal activity to run the final Release agent."""
    activity.logger.info("Executing Release activity...")
    agent = ReleaseAgent()
    with HeartbeatingStream() as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            # The release agent just needs the final approval status
            return await agent.run_agent(eval_output)

@activity.defn
async def semantic_root_cause_activity(signal: dict) -> dict:
    """Temporal activity to run the Semantic Root Cause Analysis agent."""
    activity.logger.info("Executing Semantic Root Cause Analysis activity...")
    agent = SemanticRootCauseAgent()
    with HeartbeatingStream() as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            return await agent.run_agent(signal)

@activity.defn
async def semantic_fix_proposal_activity(rca_output: dict) -> dict:
    """Temporal activity to run the Semantic Fix Proposal agent."""
    activity.logger.info("Executing Semantic Fix Proposal activity...")
    agent = SemanticFixProposalAgent()
    with HeartbeatingStream() as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            return await agent.run_agent(rca_output)

@activity.defn
async def semantic_eval_activity(fix_output: dict) -> dict:
    """Temporal activity to run the Semantic Evaluation agent."""
    activity.logger.info("Executing Semantic Evaluation activity...")
    agent = SemanticEvalAgent()
    with HeartbeatingStream() as stream:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            return await agent.run_agent(fix_output)
