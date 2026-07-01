from base_agent import BaseAgent

class FeedbackAgent(BaseAgent):
    def __init__(self):
        super().__init__(model_name="gemini-1.5-flash-latest", enable_deep_rca=False)

    async def run_agent(self, eval_output: dict) -> dict:
        """
        Runs the feedback agent to analyze the evaluation output.
        """
        # In a real scenario, this agent would perform a more complex analysis.
        # For now, it will just check the status and pass the data through.
        
        if eval_output.get("overall_status") == "success": # Changed from "status" to "overall_status" and expecting "success"
            feedback_summary = "Evaluation was successful. Feedback agent approves release."
            final_status = "APPROVED"
        else:
            feedback_summary = "Evaluation failed or had issues. Feedback agent recommends against release."
            final_status = "REJECTED"

        return {
            "status": final_status,
            "summary": feedback_summary,
            "details": eval_output, # Pass through the full evaluation output
        }
