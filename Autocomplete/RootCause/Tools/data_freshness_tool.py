from typing import Any, Dict, List
from datetime import datetime, timedelta

class DataFreshnessTool:
    def __init__(self, data_source_connector=None):
        self.data_source_connector = data_source_connector # Placeholder for a connector to various data sources

    def run(self, data_source_name: str, max_staleness_hours: int) -> Dict[str, Any]:
        """
        Checks the freshness of data in a specified autocomplete data source.
        data_source_name: The name of the data source to check (e.g., "autocomplete_index", "user_query_logs").
        max_staleness_hours: The maximum acceptable age of the data in hours.
        """
        if not self.data_source_connector:
            return {"status": "error", "summary": "Data source connector not configured."}

        try:
            # Placeholder: In a real scenario, this would connect to the actual data source
            # and fetch its last update timestamp.
            last_update_str = self.data_source_connector.get_last_update_timestamp(data_source_name)
            last_update_time = datetime.fromisoformat(last_update_str)
            
            now = datetime.now()
            staleness = now - last_update_time
            
            if staleness > timedelta(hours=max_staleness_hours):
                return {
                    "status": "stale",
                    "summary": f"Data in {data_source_name} is stale.",
                    "details": f"Last updated {staleness.total_seconds() / 3600:.2f} hours ago. Max allowed: {max_staleness_hours} hours."
                }
            else:
                return {
                    "status": "fresh",
                    "summary": f"Data in {data_source_name} is fresh.",
                    "details": f"Last updated {staleness.total_seconds() / 3600:.2f} hours ago."
                }
        except Exception as e:
            return {"status": "error", "summary": f"Failed to check freshness for {data_source_name}.", "details": str(e)}