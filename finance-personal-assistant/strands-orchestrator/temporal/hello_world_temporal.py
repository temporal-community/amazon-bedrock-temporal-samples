
import asyncio
from datetime import timedelta, datetime
from temporalio import activity, workflow

@activity.defn
async def process_data(data: str) -> str:
    """Activity that simulates work by upper-casing the payload."""
    activity.logger.info("🔧 Activity started")
    await asyncio.sleep(1)
    result = f"Processed: {data.upper()}"
    activity.logger.info("✅ Activity completed")
    return result

@workflow.defn
class HelloWorkflowTemporal:
    """Workflow that orchestrates the activity call."""

    @workflow.run
    async def run(self, name: str) -> str:
        workflow.logger.info("🚀 Workflow started")
        result = await workflow.execute_activity(
            process_data,
            args=[f"Hello {name}"],
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info("✅ Workflow finished")
        return f"Workflow result: {result}"