
from temporalio import activity

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import calculator
import matplotlib.pyplot as plt
from .models import FinancialReport


# Enhanced system prompt for structured outputs
BUDGET_SYSTEM_PROMPT = """You are a helpful personal finance assistant. 
You provide general strategies for creating budgets, tips on financial discipline to achieve financial milestones, and analyze financial trends. You do not provide any investment advice. 

When generating financial reports, always provide:
1. Clear budget breakdowns using the 50/30/20 rule or custom allocations
2. Specific, actionable recommendations (2-3 steps)
3. A financial health score based on spending patterns
4. Practical budgeting and spending advice

Please determine whether the user is in a position where they can afford to invest. If they are, provide a recommended investment amount. If they are not, provide a recommendation to save more money.

Use structured output when requested to provide comprehensive financial reports."""

# Continue with previous configurations
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name="us-west-2",
    temperature=0.0,  # Deterministic responses for financial advice
)


@tool
def calculate_budget(monthly_income: float) -> str:
    """Calculate 50/30/20 budget breakdown for the given monthly income."""
    needs = monthly_income * 0.50
    wants = monthly_income * 0.30
    savings = monthly_income * 0.20
    return f"💰 Budget for ${monthly_income:,.0f}/month:\n• Needs: ${needs:,.0f} (50%)\n• Wants: ${wants:,.0f} (30%)\n• Savings: ${savings:,.0f} (20%)"


@tool
def create_financial_chart(
    data_dict: dict, chart_title: str = "Financial Chart"
) -> str:
    """Create a pie chart visualization from financial data dictionary."""
    if not data_dict:
        return "❌ No data provided for chart"

    labels = list(data_dict.keys())
    values = list(data_dict.values())
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57", "#FF9FF3"]

    plt.figure(figsize=(8, 6))
    plt.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        colors=colors[: len(values)],
        startangle=90,
    )
    plt.title(f"📊 {chart_title}", fontsize=14, fontweight="bold")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()

    return f"✅ {chart_title} visualization created!"


# Create our complete financial agent
budget_agent = Agent(
    model=bedrock_model,
    system_prompt=BUDGET_SYSTEM_PROMPT,
    tools=[calculate_budget, create_financial_chart, calculator],
    callback_handler=None,
)

@activity.defn
async def budget_agent_activity(prompt: str) -> FinancialReport:
    """Activity that uses the budget agent to generate a financial report."""
    activity.logger.info("Budget Agent Activity started")

        # Test structured output using structured_output_async
    print("\nStructured financial report:")
    structured_response = budget_agent.structured_output(
        output_model=FinancialReport,
        prompt=prompt,
    )
    print(f"Income: ${structured_response.monthly_income:,.0f}")
    for category in structured_response.budget_categories:
        print(
            f"• {category.name}: ${category.amount:,.0f} ({category.percentage:.1f}%)"
        )
    print(f"\nFinancial Health Score: {structured_response.financial_health_score}/10")
    print("\nRecommendations:")
    for i, rec in enumerate(structured_response.recommendations, 1):
        print(f"{i}. {rec}")

    activity.logger.info("✅ Budget Agent Activity completed")
    return structured_response