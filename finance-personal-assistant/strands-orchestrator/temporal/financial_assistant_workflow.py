
import asyncio
from datetime import timedelta, datetime
from temporalio import workflow
from .models import FinancialReport, BedrockInvocationRequest

@workflow.defn
class FinancialAssistantWorkflow:
    """Workflow that orchestrates the activity calls."""

    def __init__(self):
        self.recommended_investment_amount: float | None = None
        self.requested_investment_amount: float | None = None

    @workflow.signal
    async def set_investment_amount(self, amount: float) -> None:
        """Signal handler to set the requested investment amount."""
        self.requested_investment_amount = amount
        workflow.logger.info(f"✅ Received signal: requested_investment_amount set to {amount}")

    @workflow.query
    def get_recommended_investment_amount(self) -> float | None:
        """Query handler to get the recommended investment amount."""
        return self.recommended_investment_amount

    @workflow.run
    async def run(self, prompt: str) -> str:
        workflow.logger.info("🚀 Workflow started")
        
        # First, execute the budget agent activity
        budget_result = await workflow.execute_activity(
            "budget_agent_activity",
            args=[prompt],
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info("✅ Budget agent activity completed")
        
        # Reconstruct FinancialReport from dict (Temporal deserializes Pydantic models to dicts)
        if isinstance(budget_result, dict):
            financial_report = FinancialReport(**budget_result)
        else:
            financial_report = budget_result
        
        # Store the recommended investment amount in local state
        self.recommended_investment_amount = financial_report.recommended_investment_amount
        workflow.logger.info(f"✅ Stored recommended_investment_amount: {self.recommended_investment_amount}")
        
        # Convert FinancialReport to JSON string using Pydantic's built-in method
        report_json = financial_report.model_dump_json(indent=2)
        
        # Define system prompt for formatting
        system_prompt = "You are a helpful assistant that formats financial reports in a clear, professional, and easy-to-read format."
        
        # Create user prompt with the financial report data
        user_prompt = f"""Please format the following financial report data into clear, readable text:

{report_json}"""
        
        # Create Bedrock invocation request with separated system prompt and user prompt
        bedrock_request = BedrockInvocationRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            region_name="us-west-2",
            max_tokens=2000,
        )
        
        # Then, format the result using the generic LLM activity
        formatted_result = await workflow.execute_activity(
            "invoke_bedrock_model",
            args=[bedrock_request],
            start_to_close_timeout=timedelta(seconds=30),
        )
        workflow.logger.info("✅ LLM format activity for the budget report completed")

        # Wait for requested_investment_amount to be set via signal
        workflow.logger.info("⏳ Waiting for requested_investment_amount signal...")
        await workflow.wait_condition(lambda: self.requested_investment_amount is not None)
        workflow.logger.info(f"✅ Received requested_investment_amount: {self.requested_investment_amount}")

        if self.requested_investment_amount > 0:
            financial_analysis_result = await workflow.execute_activity(
                "financial_analysis_activity",
                args=[self.requested_investment_amount],
                start_to_close_timeout=timedelta(seconds=30),
            )
            workflow.logger.info("✅ Financial analysis activity completed")

            # Create Bedrock invocation request with separated system prompt and user prompt
            bedrock_request = BedrockInvocationRequest(
                prompt=financial_analysis_result,
                system_prompt="You are a helpful assistant that formats financial analysis results in a clear, professional, and easy-to-read format.",
                model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                region_name="us-west-2",
                max_tokens=2000,
            )
            
            # Then, format the result using the generic LLM activity
            financial_analysis_formatted_result = await workflow.execute_activity(
                "invoke_bedrock_model",
                args=[bedrock_request],
                start_to_close_timeout=timedelta(seconds=30),
            )
            workflow.logger.info("✅ LLM format activity for the budget report completed")

            result = f"{formatted_result}\n\n{financial_analysis_formatted_result}"
        else:
            result = formatted_result
        workflow.logger.info("✅ Workflow finished")
        
        return result