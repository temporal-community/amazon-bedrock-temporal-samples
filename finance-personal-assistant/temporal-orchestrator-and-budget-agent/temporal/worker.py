# ABOUTME: Temporal worker for the financial assistant with OpenAI Agents SDK integration.
# ABOUTME: Registers workflows and activities, including the OpenAI-based budget agent.

import asyncio
import os
from datetime import timedelta

from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin, ModelActivityParameters
from temporalio.worker import Worker

from .financial_assistant_workflow import FinancialAssistantWorkflow
from .budget_agent_workflow import BudgetAgentWorkflow
from .budget_activities import calculate_budget, calculator
from .financial_analysis_activity import financial_analysis_activity
from .llm_activity import invoke_bedrock_model


async def main():
    # Get Temporal configuration from environment variables
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "us-east-1.aws.api.temporal.io:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")

    print(f"Connecting to Temporal Cloud at {temporal_address}...")
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
    print("Connected to Temporal Cloud")

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


if __name__ == "__main__":
    asyncio.run(main())
