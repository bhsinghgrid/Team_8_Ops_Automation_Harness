import asyncio
import os
import sys
import logging
from temporalio.client import Client
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def wait_for_temporal_server():
    load_dotenv()
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    max_retries = 60  # Try for up to 2 minutes (2 seconds * 60 retries)
    retry_delay = 2   # seconds

    logger.info(f"Waiting for Temporal server at {temporal_address}...")

    for i in range(max_retries):
        try:
            client = await Client.connect(temporal_address)
            await client.close()
            logger.info("Successfully connected to Temporal server.")
            return
        except Exception as e:
            logger.warning(f"Attempt {i+1}/{max_retries}: Temporal server not ready. Retrying in {retry_delay}s. Error: {e}")
            await asyncio.sleep(retry_delay)
    
    logger.error(f"Failed to connect to Temporal server after {max_retries} attempts.")
    sys.exit(1)

if __name__ == "__main__":
    asyncio.run(wait_for_temporal_server())
