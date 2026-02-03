# ABOUTME: Pydantic models for structured outputs from agents.
# ABOUTME: Defines FinancialReport and BudgetCategory for budget agent responses.

from typing import List
from pydantic import BaseModel, Field


class BudgetCategory(BaseModel):
    """Budget category model."""
    name: str = Field(description="Budget category name")
    amount: float = Field(description="Dollar amount for this category")
    percentage: float = Field(description="Percentage of total income")


class FinancialReport(BaseModel):
    """Financial report model."""
    monthly_income: float = Field(description="Total monthly income")
    budget_categories: List[BudgetCategory] = Field(
        description="List of budget categories"
    )
    recommendations: List[str] = Field(description="List of specific recommendations")
    financial_health_score: int = Field(
        ge=1, le=10, description="Financial health score from 1-10"
    )
    recommended_investment_amount: float = Field(
        default=0,
        description="Recommended investment amount"
    )
