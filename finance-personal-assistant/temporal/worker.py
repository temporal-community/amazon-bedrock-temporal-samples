import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from .financial_assistant_workflow import FinancialAssistantWorkflow
from .budget_agent_activity import budget_agent_activity
from .financial_analysis_activity import financial_analysis_activity
from .llm_activity import invoke_bedrock_model
from temporalio.contrib.pydantic import pydantic_data_converter


async def main():

    # Get Temporal configuration from environment variables
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "us-east-1.aws.api.temporal.io:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY") 

    print(f"Connecting to Temporal Cloud at {temporal_address}...")
    client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
        tls=True,  # Enable TLS for cloud connection
        rpc_metadata={
            "authorization": f"Bearer {temporal_api_key}"
        },
        data_converter=pydantic_data_converter
    )
    print("✅ Connected to Temporal Cloud")

    worker = Worker(
        client,
        task_queue="financial-assistant-task-queue",
        workflows=[
            FinancialAssistantWorkflow,
        ],
        activities=[
            budget_agent_activity,
            invoke_bedrock_model,
            financial_analysis_activity,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
