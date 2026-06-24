# test_eval_agent.py
import asyncio
import json
import sys
import os

# Ensure the root directory is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Catalog.Eval.eval_agent import GoogleEvalAgent

async def main():
    print("\n--- Testing GoogleEvalAgent ---")
    try:
        agent = GoogleEvalAgent()
        print("✅ GoogleEvalAgent instantiated successfully")

        # In a real pipeline, this would receive the Diffy report ID from a CI/CD job
        # This mock ID will trigger the mock response in the DiffyApiTool
        input_signal = {
            "diff_id": "c28b-4b1e-b3f9-7153d3e690f3", 
            "context": "Catalog coverage gap patched for Trailhead XT footwear."
        }

        result = await agent.run_agent(input_signal)
        
        print("\n✅ GoogleEvalAgent ran successfully")
        print("\n--- Agent Output ---")
        print(json.dumps(result, indent=2))
        print("\n--- Test Complete ---")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
