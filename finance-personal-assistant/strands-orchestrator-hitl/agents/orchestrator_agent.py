# ABOUTME: Orchestrator agent that coordinates budget and financial analysis agents.
# ABOUTME: Configured for human-in-the-loop by asking for confirmation before investment analysis.

from strands import Agent, tool
from strands.models import BedrockModel

from .budget_agent import budget_agent
from .financial_analysis_agent import financial_analysis_agent
from .models import FinancialReport


ORCHESTRATOR_PROMPT = """You are a financial advisory orchestrator that coordinates specialized agents to provide comprehensive financial guidance.

You have access to two specialized agents:

1. **budget_agent_tool**: Use this for questions about:
   - Creating budgets and budget breakdowns
   - Analyzing spending habits and expenses
   - Financial health assessments
   - Savings recommendations
   - Determining if someone can afford to invest

2. **financial_analysis_agent_tool**: Use this for questions about:
   - Stock analysis and research
   - Investment portfolio recommendations
   - Comparing stock performance
   - Market data and trends

**Routing Guidelines:**
- For budget-only questions, use only the budget_agent_tool
- For investment-only questions (where the user provides a specific amount), use only the financial_analysis_agent_tool
- For comprehensive financial planning (e.g., "create a financial plan", "help me with my finances"):
  1. First call budget_agent_tool to analyze the user's financial situation
  2. Present the budget analysis results to the user
  3. IMPORTANT: After presenting the budget analysis, you MUST ask the user to confirm how much they want to invest before proceeding. DO NOT automatically call the financial_analysis_agent_tool.
  4. Wait for the user to respond with their desired investment amount in a follow-up message
  5. Only call financial_analysis_agent_tool AFTER the user explicitly confirms an investment amount

**Human-in-the-Loop Protocol:**
When the budget analysis recommends an investment amount, always respond with something like:
"Based on your budget analysis, I recommend investing $X per month. Would you like me to create an investment portfolio? If so, please confirm how much you'd like to invest."

Then STOP and wait for the user's response. Do not proceed to investment analysis until the user confirms.

Always present information in a clear, professional format."""


bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name="us-west-2",
    temperature=0.0,
)


@tool
def budget_agent_tool(query: str) -> str:
    """
    Call the budget agent for budget analysis, spending habits, and financial health assessment.
    Returns a structured financial report with budget breakdown, recommendations, and investment advice.
    """
    report: FinancialReport = budget_agent.structured_output(
        output_model=FinancialReport,
        prompt=query,
    )

    # Format the report as a readable string
    result = f"""
=== Budget Analysis Report ===

Monthly Income: ${report.monthly_income:,.0f}

Budget Breakdown:
"""
    for category in report.budget_categories:
        result += f"  • {category.name}: ${category.amount:,.0f} ({category.percentage:.1f}%)\n"

    result += f"""
Financial Health Score: {report.financial_health_score}/10

Recommendations:
"""
    for i, rec in enumerate(report.recommendations, 1):
        result += f"  {i}. {rec}\n"

    result += f"""
Recommended Investment Amount: ${report.recommended_investment_amount:,.0f}
"""
    return result


@tool
def financial_analysis_agent_tool(query: str, investment_amount: float = 0) -> str:
    """
    Call the financial analysis agent for investment research and portfolio recommendations.
    Provide the investment_amount if known (e.g., from user confirmation after budget analysis).
    """
    if investment_amount > 0:
        prompt = f"{query}. The available investment amount is ${investment_amount:,.0f}."
    else:
        prompt = query

    response = financial_analysis_agent(prompt=prompt)
    return response.message["content"][0]["text"]


# Create the orchestrator agent
orchestrator_agent = Agent(
    model=bedrock_model,
    system_prompt=ORCHESTRATOR_PROMPT,
    tools=[budget_agent_tool, financial_analysis_agent_tool],
    callback_handler=None,
)
