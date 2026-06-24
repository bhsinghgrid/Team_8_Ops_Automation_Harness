# standalone_test.py

from Catalog.RootCause.google_agent import GoogleRootCauseAgent
import asyncio

async def main():
    agent = GoogleRootCauseAgent()

    result = await agent.run_agent(
        {"signal_type": "catalog"}
    )

    print(result)

asyncio.run(main())
