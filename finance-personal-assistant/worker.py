"""AgentCore entrypoint for the on-demand Temporal finance Worker."""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from temporalio.client import Client
from temporalio.common import VersioningBehavior
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import (
    ActivityInboundInterceptor,
    ExecuteActivityInput,
    Interceptor,
    Worker,
    WorkerDeploymentConfig,
    WorkerDeploymentVersion,
)

from temporal.budget_agent_activity import budget_agent_activity
from temporal.financial_analysis_activity import financial_analysis_activity
from temporal.financial_assistant_workflow import FinancialAssistantWorkflow
from temporal.llm_activity import invoke_bedrock_model

app = BedrockAgentCoreApp()
log = app.logger
_worker: asyncio.Task[None] | None = None

TASK_QUEUE = "financial-assistant-task-queue"
DEPLOYMENT_NAME = "finance-personal-assistant"
IDLE_SECONDS = float(os.environ.get("AGENTCORE_DEBOUNCE_SECONDS", "60"))
DRAIN_TIMEOUT = timedelta(seconds=120)


class ActivityTracker(Interceptor):
    """Wait for a quiet period without interrupting an in-flight Activity."""

    def __init__(self) -> None:
        self.inflight = 0
        self.changed = asyncio.Event()

    def intercept_activity(
        self, next: ActivityInboundInterceptor
    ) -> ActivityInboundInterceptor:
        return _TrackedActivity(next, self)

    async def wait_until_idle(self, seconds: float) -> None:
        while True:
            self.changed.clear()
            try:
                await asyncio.wait_for(self.changed.wait(), timeout=seconds)
            except asyncio.TimeoutError:
                if self.inflight == 0:
                    return


class _TrackedActivity(ActivityInboundInterceptor):
    def __init__(self, next: ActivityInboundInterceptor, tracker: ActivityTracker):
        super().__init__(next)
        self.tracker = tracker

    async def execute_activity(self, input: ExecuteActivityInput):
        self.tracker.inflight += 1
        self.tracker.changed.set()
        try:
            return await self.next.execute_activity(input)
        finally:
            self.tracker.inflight -= 1
            self.tracker.changed.set()


def _load_api_key() -> str:
    secret_arn = os.environ["TEMPORAL_API_KEY_SECRET_ARN"]
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    value = boto3.client("secretsmanager", region_name=region).get_secret_value(
        SecretId=secret_arn
    )
    return value["SecretString"]


async def run_temporal_worker() -> None:
    """Poll the Task Queue until the Worker has been idle, then drain it."""
    build_id = os.environ["TEMPORAL_BUILD_ID"]
    api_key = await asyncio.to_thread(_load_api_key)
    client = await Client.connect(
        os.environ["TEMPORAL_ADDRESS"],
        namespace=os.environ["TEMPORAL_NAMESPACE"],
        api_key=api_key,
        tls=True,
        data_converter=pydantic_data_converter,
    )
    tracker = ActivityTracker()
    log.info("Polling %s as %s/%s", TASK_QUEUE, DEPLOYMENT_NAME, build_id)
    with ThreadPoolExecutor(max_workers=4) as activity_executor:
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[FinancialAssistantWorkflow],
            activities=[
                budget_agent_activity,
                invoke_bedrock_model,
                financial_analysis_activity,
            ],
            activity_executor=activity_executor,
            interceptors=[tracker],
            deployment_config=WorkerDeploymentConfig(
                version=WorkerDeploymentVersion(
                    deployment_name=DEPLOYMENT_NAME, build_id=build_id
                ),
                use_worker_versioning=True,
                default_versioning_behavior=VersioningBehavior.PINNED,
            ),
            graceful_shutdown_timeout=DRAIN_TIMEOUT,
        )
        async with worker:
            await tracker.wait_until_idle(IDLE_SECONDS)
    log.info("Worker drained after %s idle seconds", IDLE_SECONDS)


async def _run_until_idle(task_id: int) -> None:
    try:
        await run_temporal_worker()
    except Exception:
        log.exception("Temporal Worker failed")
    finally:
        app.complete_async_task(task_id)


@app.entrypoint
async def invoke(payload: dict) -> dict:
    """Acknowledge a capacity request while the Worker polls in the background."""
    global _worker
    if _worker is not None and not _worker.done():
        return {"message": "worker already polling", "task_queue": TASK_QUEUE}

    task_id = app.add_async_task("temporal-worker")
    _worker = asyncio.create_task(_run_until_idle(task_id))
    return {"message": "worker starting", "task_queue": TASK_QUEUE}


if __name__ == "__main__":
    app.run()
