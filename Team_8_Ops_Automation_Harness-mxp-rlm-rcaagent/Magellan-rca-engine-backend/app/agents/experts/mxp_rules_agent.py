import json
from google import genai
from google.genai import types
from app.schemas.rca_schema import EvidencePackOutput, RootCauseDetails
from app.core.prompts.mxp_prompts import MXP_SYSTEM_PROMPT, MXP_USER_PROMPT_TEMPLATE
from app.schemas.shared_ingress import IncomingSignal

class MXPRulesAgent:
    def __init__(self, context_builder, gemini_client):
        self.context_builder = context_builder
        self.client = gemini_client
        self.model = 'gemini-2.5-flash'
        
        # Manually defining the schema to bypass the 'additionalProperties' API restriction
        self.response_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "capability": types.Schema(type=types.Type.STRING, description="The capability domain."),
                "symptom": types.Schema(type=types.Type.STRING, description="Summary of the anomaly."),
                "root_cause": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "primary_cause": types.Schema(type=types.Type.STRING, description="The primary failure logic."),
                        "confidence_score": types.Schema(type=types.Type.NUMBER, description="Confidence score from 0.0 to 1.0"),
                        "supporting_evidence": types.Schema(
                            type=types.Type.OBJECT, 
                            properties={
                                "rule_id": types.Schema(type=types.Type.STRING),
                                "created_by": types.Schema(type=types.Type.STRING),
                                "deployed_at": types.Schema(type=types.Type.STRING),
                                "warehouse_stock": types.Schema(type=types.Type.INTEGER)
                            }
                        )
                    },
                    required=["primary_cause", "confidence_score", "supporting_evidence"]
                )
            },
            required=["capability", "symptom", "root_cause"]
        )

    def analyze(self, signal: IncomingSignal) -> EvidencePackOutput:
        """Analyzes context using the new google-genai SDK."""
        context_data = self.context_builder.gather_context(signal)
        
        prompt = MXP_USER_PROMPT_TEMPLATE.format(
            query=context_data["query"],
            product_id=context_data["product_id"],
            ctr_context=json.dumps(context_data["performance_metrics"], indent=4),
            rules_context=json.dumps(context_data["investigation_tools"], indent=4),
        )

        try:
            # We use the manually constructed schema here
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=MXP_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=self.response_schema,
                    temperature=0.1
                )
            )
            
            # Since we passed a manual schema, we parse the text back into our Pydantic model
            evidence_pack = EvidencePackOutput.model_validate_json(response.text)
            evidence_pack.signal_id = signal.signal_id
            return evidence_pack

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return EvidencePackOutput(
                signal_id=signal.signal_id,
                capability="Error",
                symptom="Failed to analyze anomaly",
                root_cause=RootCauseDetails(
                    primary_cause=str(e),
                    confidence_score=0.0,
                    supporting_evidence={},
                ),
            )