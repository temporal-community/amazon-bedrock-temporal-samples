# ABOUTME: Temporal activities for budget agent tools.
# ABOUTME: These activities are wrapped as tools for the OpenAI Agents SDK budget agent.

from typing import List
from temporalio import activity
import matplotlib.pyplot as plt
from pydantic import BaseModel


class ChartDataItem(BaseModel):
    """A single data item for the financial chart."""
    category: str
    amount: float


@activity.defn
async def calculate_budget(monthly_income: float) -> str:
    """Calculate 50/30/20 budget breakdown for the given monthly income.

    Args:
        monthly_income: The monthly income amount in dollars.

    Returns:
        A formatted string with the budget breakdown.
    """
    needs = monthly_income * 0.50
    wants = monthly_income * 0.30
    savings = monthly_income * 0.20
    return f"Budget for ${monthly_income:,.0f}/month:\n• Needs: ${needs:,.0f} (50%)\n• Wants: ${wants:,.0f} (30%)\n• Savings: ${savings:,.0f} (20%)"


@activity.defn
async def create_financial_chart(data_items: List[ChartDataItem], chart_title: str) -> str:
    """Create a pie chart visualization from financial data.

    Args:
        data_items: List of chart data items with category and amount.
        chart_title: Title for the chart.

    Returns:
        A confirmation message.
    """
    if not data_items:
        return "No data provided for chart"

    labels = [item.category for item in data_items]
    values = [item.amount for item in data_items]
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57", "#FF9FF3"]

    plt.figure(figsize=(8, 6))
    plt.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        colors=colors[: len(values)],
        startangle=90,
    )
    plt.title(f"{chart_title}", fontsize=14, fontweight="bold")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()

    return f"{chart_title} visualization created!"


@activity.defn
async def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A mathematical expression to evaluate (e.g., "100 * 0.5 + 50").

    Returns:
        The result of the calculation as a string.
    """
    try:
        # Use eval with restricted builtins for safety
        allowed_names = {"__builtins__": {}}
        result = eval(expression, allowed_names, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"
