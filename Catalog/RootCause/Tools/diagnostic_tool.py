from .catalog_repository import CatalogRepository
from .catalog_coverage_tool import CatalogCoverageTool
from .schema_validation import CatalogSchemaValidationTool
from .freshness import CatalogFreshnessTool
from .search_Quality import CatalogSearchQualityTool

class ComprehensiveDiagnosticTool:
    """
    A single tool that runs multiple diagnostic checks in a batch to improve efficiency.
    """
    def __init__(self, repository: CatalogRepository):
        self.repository = repository
        self.coverage_tool = CatalogCoverageTool(repository)
        self.schema_tool = CatalogSchemaValidationTool(repository)
        self.freshness_tool = CatalogFreshnessTool(repository)
        self.quality_tool = CatalogSearchQualityTool(repository)

    def run(self, signal_data: dict) -> dict:
        """
        Runs a batch of diagnostic tools and returns an aggregated report.
        """
        print("--- Running Comprehensive Diagnostic Batch Tool ---")
        
        # Run all diagnostic tools
        coverage_report = self.coverage_tool.run(signal_data=signal_data)
        schema_report = self.schema_tool.run(signal_data=signal_data)
        freshness_report = self.freshness_tool.run(signal_data=signal_data)
        quality_report = self.quality_tool.run(signal_data=signal_data)
        
        # Aggregate the results into a single report
        aggregated_report = {
            "diagnostic_summary": "Aggregated report from batched diagnostic tools.",
            "coverage_analysis": coverage_report,
            "schema_analysis": schema_report,
            "freshness_analysis": freshness_report,
            "quality_analysis": quality_report
        }
        
        print(f"--- Comprehensive Diagnostic Complete. ---")
        return aggregated_report

