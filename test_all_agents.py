# test_all_agents.py
import asyncio
import sys
import os

# Ensure the root directory is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("--- Testing Agent Instantiation ---")

async def test_agents():
    agents_to_test = {
        "GoogleRootCauseAgent": "Catalog.RootCause.google_agent",
        "GoogleFixProposalAgent": "Catalog.Fix_Proposal.fix_agent",
        "GoogleEvalAgent": "Catalog.Eval.eval_agent",
        "AutocompleteRootCauseAgent": "Autocomplete.RootCause.main_agent",
        "AutocompleteFixProposalAgent": "Autocomplete.Fix_Proposal.fix_agent",
        "AutocompleteEvalAgent": "Autocomplete.Eval.eval_agent",
        "SemanticRootCauseAgent": "Semantic.RootCause.main_agent",
        "SemanticFixProposalAgent": "Semantic.Fix_Proposal.fix_agent",
        "SemanticEvalAgent": "Semantic.Eval.eval_agent",
        "ReleaseAgent": "Release.release_agent",
        "FeedbackAgent": "Feedback.feedback_agent",
    }

    all_successful = True

    for class_name, module_path in agents_to_test.items():
        try:
            # Dynamically import the module and get the class
            module = __import__(module_path.replace("/", "."), fromlist=[class_name])
            AgentClass = getattr(module, class_name)
            
            # Instantiate the agent
            agent = AgentClass()
            print(f"✅ {class_name} instantiated successfully")
        except Exception as e:
            print(f"❌ Failed to instantiate {class_name}: {e}")
            all_successful = False

    print("\n--- Agent Instantiation Test Complete ---")
    if not all_successful:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_agents())
