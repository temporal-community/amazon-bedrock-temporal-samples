import asyncio
import os
import sys
import uuid

from temporalio.client import Client

from .financial_assistant_workflow import FinancialAssistantWorkflow
from temporalio.contrib.pydantic import pydantic_data_converter


def is_guid(s: str) -> bool:
    """Check if a string is a valid GUID/UUID."""
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


async def main():
    # Get input string from command line argument or prompt
    if len(sys.argv) > 1:
        input_string = sys.argv[1]
    else:
        input_string = input("Enter a string (GUID to connect to existing workflow, or any string to start new): ").strip()

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

    workflow_id = None
    workflow_handle = None

    if is_guid(input_string):
        # Get handle to existing workflow that ends with this GUID
        # We'll search for workflows with this GUID suffix
        # For now, we'll construct the workflow ID assuming it ends with the GUID
        workflow_id = f"financial-assistant-workflow-{input_string}"
        workflow_handle = client.get_workflow_handle(workflow_id)
        print(f"✅ Connected to existing workflow: {workflow_id}")
        
        # Query for recommended investment amount
        try:
            recommended_amount = await workflow_handle.query("get_recommended_investment_amount")
            if recommended_amount is not None:
                print(f"💰 Recommended investment amount: ${recommended_amount:,.2f}")
            else:
                print("ℹ️  Recommended investment amount not yet available")
        except Exception as e:
            print(f"⚠️  Could not query recommended investment amount: {e}")
    else:
        # Start a new workflow with a new GUID appended to the workflow ID
        new_guid = str(uuid.uuid4())
        workflow_id = f"financial-assistant-workflow-{new_guid}"
        
        workflow_handle = await client.start_workflow(
            FinancialAssistantWorkflow.run,
            "Generate a comprehensive financial report for someone earning $6000/month with $800 dining expenses.",
            id=workflow_id,
            task_queue="financial-assistant-task-queue",
        )
        print(f"✅ Started new workflow: {workflow_id}")

    # Start a background task to wait for workflow completion
    workflow_result_task = asyncio.create_task(workflow_handle.result())
    
    # Enter loop waiting for user input
    print("\nCommands:")
    print("  - Enter a number to send as a signal to the workflow")
    print("  - 'query' or 'recommended' to get the recommended investment amount")
    print("  - 'quit' or 'exit' to exit")
    while True:
        try:
            # Check if workflow has completed
            if workflow_result_task.done():
                try:
                    result = await workflow_result_task
                    print("\n" + "="*80)
                    print("✅ Workflow completed!")
                    print("="*80)
                    print(result)
                    print("="*80)
                    break
                except Exception as e:
                    print(f"\n❌ Workflow completed with error: {e}")
                    break
            
            user_input = input("> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Exiting...")
                workflow_result_task.cancel()
                break
            
            # Handle query command
            if user_input.lower() in ['query', 'recommended', 'rec']:
                try:
                    recommended_amount = await workflow_handle.query("get_recommended_investment_amount")
                    if recommended_amount is not None:
                        print(f"💰 Recommended investment amount: ${recommended_amount:,.2f}")
                    else:
                        print("ℹ️  Recommended investment amount not yet available")
                except Exception as e:
                    print(f"⚠️  Could not query recommended investment amount: {e}")
                continue
            
            # Try to parse as a number
            try:
                number = float(user_input)
                # Send signal to the workflow
                await workflow_handle.signal("set_investment_amount", number)
                print(f"✅ Sent signal with number: {number}")
                
                # Check again if workflow completed after sending signal
                if workflow_result_task.done():
                    try:
                        result = await workflow_result_task
                        print("\n" + "="*80)
                        print("✅ Workflow completed!")
                        print("="*80)
                        print(result)
                        print("="*80)
                        break
                    except Exception as e:
                        print(f"\n❌ Workflow completed with error: {e}")
                        break
            except ValueError:
                print(f"⚠️  '{user_input}' is not a valid number. Please enter a number, 'query', or 'quit' to exit.")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
