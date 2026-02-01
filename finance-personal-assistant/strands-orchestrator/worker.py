import asyncio
import os
import logging

from temporalio.client import Client
from temporalio.worker import Worker

# Import from temporal directory
from temporal.financial_assistant_workflow import FinancialAssistantWorkflow
from temporal.budget_agent_activity import budget_agent_activity
from temporal.financial_analysis_activity import financial_analysis_activity
from temporal.llm_activity import invoke_bedrock_model
from temporalio.contrib.pydantic import pydantic_data_converter

from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
client = None
worker_task = None

async def run_temporal_worker():
    global client

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.entrypoint
async def invoke(payload):
    """AgentCore entrypoint that starts the Temporal worker if not already running."""
    global worker_task
    
    if worker_task is None or worker_task.done():
        # Start the worker in the background
        worker_task = asyncio.create_task(run_temporal_worker())
        logger.info("🚀 Temporal worker started")
        return "worker started"
    else:
        logger.info("✅ Temporal worker already running - keeping alive")
        return "worker kept alive"

if __name__ == "__main__":
    app.run()