# ABOUTME: Budget agent workflow using OpenAI Agents SDK with Temporal durability.
# ABOUTME: Wraps budget-related activities as tools for the AI agent.

from __future__ import annotations

import json
from datetime import timedelta

from temporalio.contrib import openai_agents as temporal_agents
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from agents import Agent, Runner
    from temporal.budget_activities import calculate_budget, calculator


BUDGET_SYSTEM_PROMPT = """You are a helpful personal finance assistant.
You provide general strategies for creating budgets, tips on financial discipline to achieve financial milestones, and analyze financial trends. You do not provide any investment advice.

When generating financial reports, always provide:
1. Clear budget breakdowns using the 50/30/20 rule or custom allocations
2. Specific, actionable recommendations (2-3 steps)
3. A financial health score based on spending patterns (1-10)
4. Practical budgeting and spending advice

Please determine whether the user is in a position where they can afford to invest. If they are, provide a recommended investment amount. If they are not, provide a recommendation to save more money.

IMPORTANT: Your final response MUST be valid JSON in this exact format:
{
    "monthly_income": <number>,
    "budget_categories": [
        {"name": "<category name>", "amount": <number>, "percentage": <number>}
    ],
    "recommendations": ["<recommendation 1>", "<recommendation 2>", ...],
    "financial_health_score": <integer 1-10>,
    "recommended_investment_amount": <number>
}

Use the available tools to calculate budget breakdowns as needed."""


@workflow.defn
class BudgetAgentWorkflow:
    """Workflow that runs the budget agent with durable tool execution."""

    @workflow.run
    async def run(self, prompt: str) -> dict:
        """Run the budget agent and return structured financial report data.

        Args:
            prompt: The user's financial query/information.

        Returns:
            A dictionary representing the FinancialReport structure.
        """
        workflow.logger.info("Budget Agent Workflow started")

        agent = Agent(
            name="Budget Agent",
            instructions=BUDGET_SYSTEM_PROMPT,
            model="gpt-4o",
            tools=[
                temporal_agents.workflow.activity_as_tool(
                    calculate_budget, start_to_close_timeout=timedelta(seconds=30)
                ),
                temporal_agents.workflow.activity_as_tool(
                    calculator, start_to_close_timeout=timedelta(seconds=30)
                ),
            ],
        )

        result = await Runner.run(agent, input=prompt)
        workflow.logger.info("Budget Agent completed")

        # Parse the JSON response into a dictionary
        try:
            # Try to extract JSON from the response
            output = result.final_output
            # Find JSON in the response (it might be wrapped in markdown code blocks)
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                output = output[json_start:json_end].strip()
            elif "```" in output:
                json_start = output.find("```") + 3
                json_end = output.find("```", json_start)
                output = output[json_start:json_end].strip()

            financial_report = json.loads(output)
            workflow.logger.info("Successfully parsed financial report JSON")
            return financial_report
        except json.JSONDecodeError as e:
            workflow.logger.error(f"Failed to parse JSON response: {e}")
            # Return a default structure if parsing fails
            return {
                "monthly_income": 0,
                "budget_categories": [],
                "recommendations": [f"Error parsing response: {result.final_output}"],
                "financial_health_score": 1,
                "recommended_investment_amount": 0,
            }
