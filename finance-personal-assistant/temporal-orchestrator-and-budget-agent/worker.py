# ABOUTME: AgentCore entrypoint for the Temporal-orchestrated financial assistant.
# ABOUTME: Starts the Temporal worker with OpenAI Agents SDK integration for the budget agent.

import asyncio
import os
import logging
from datetime import timedelta

from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin, ModelActivityParameters
from temporalio.worker import Worker

from temporal.financial_assistant_workflow import FinancialAssistantWorkflow
from temporal.budget_agent_workflow import BudgetAgentWorkflow
from temporal.budget_activities import calculate_budget, calculator
from temporal.financial_analysis_activity import financial_analysis_activity
from temporal.llm_activity import invoke_bedrock_model

from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
client = None
worker_task = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_temporal_worker():
    global client

    # Get Temporal configuration from environment variables
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "us-east-1.aws.api.temporal.io:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")

    logger.info(f"Connecting to Temporal Cloud at {temporal_address}...")
    client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
        tls=True,
        rpc_metadata={
            "authorization": f"Bearer {temporal_api_key}"
        },
        plugins=[
            OpenAIAgentsPlugin(
                model_params=ModelActivityParameters(
                    start_to_close_timeout=timedelta(seconds=90),
                    schedule_to_close_timeout=timedelta(seconds=500),
                    retry_policy=RetryPolicy(
                        backoff_coefficient=2.0,
                        initial_interval=timedelta(seconds=1),
                        maximum_interval=timedelta(seconds=5),
                    ),
                )
            ),
        ],
    )
    logger.info("Connected to Temporal Cloud")

    worker = Worker(
        client,
        task_queue="financial-assistant-task-queue",
        workflows=[
            FinancialAssistantWorkflow,
            BudgetAgentWorkflow,
        ],
        activities=[
            # Budget agent activities (tools)
            calculate_budget,
            calculator,
            # Other activities
            invoke_bedrock_model,
            financial_analysis_activity,
        ],
    )
    await worker.run()


@app.entrypoint
async def invoke(payload):
    """AgentCore entrypoint that starts the Temporal worker if not already running."""
    global worker_task

    if worker_task is None or worker_task.done():
        # Start the worker in the background
        worker_task = asyncio.create_task(run_temporal_worker())
        logger.info("Temporal worker started")
        return "worker started"
    else:
        logger.info("Temporal worker already running - keeping alive")
        return "worker kept alive"


if __name__ == "__main__":
    app.run()
