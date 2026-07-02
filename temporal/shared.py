import io
import time
from temporalio import activity

class HeartbeatingStream(io.StringIO):
    """
    An in-memory stream that sends its contents as Temporal heartbeats.
    This is useful for capturing logs from a long-running process and
    making them visible in the Temporal UI.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_heartbeat_time = 0.0

    def write(self, s):
        if s and s.strip():
            # Temporal has a size limit on heartbeat details, so we truncate.
            details = s[:2000]
            current_time = time.time()
            # Throttle heartbeats to once every 2 seconds to prevent asyncio.queues.QueueFull
            if current_time - self._last_heartbeat_time >= 2.0:
                try:
                    activity.heartbeat(details)
                    self._last_heartbeat_time = current_time
                    # Also log to the worker's console for local debugging.
                    print(details)
                except Exception:
                    # This will be thrown if not in an activity context, which is fine.
                    pass
        super().write(s)
