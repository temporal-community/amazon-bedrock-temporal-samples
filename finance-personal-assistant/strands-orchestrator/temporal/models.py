from typing import Optional, List
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
        description="Recommended investment amount")


class MessageContent(BaseModel):
    """Content block for a message."""
    type: str = Field(default="text", description="Content type")
    text: str = Field(description="Text content")


class Message(BaseModel):
    """Message in a conversation."""
    role: str = Field(description="Message role: 'user' or 'assistant'")
    content: List[MessageContent] = Field(description="Message content blocks")


class BedrockInvocationRequest(BaseModel):
    """Request structure for invoking a Bedrock model."""
    prompt: Optional[str] = Field(
        default=None,
        description="The text prompt to send to the model (used if messages not provided)"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt to set the model's behavior"
    )
    messages: Optional[List[Message]] = Field(
        default=None,
        description="Array of messages for conversation history"
    )
    model_id: str = Field(
        default="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        description="The Bedrock model ID to use"
    )
    region_name: str = Field(
        default="us-west-2",
        description="AWS region for the Bedrock runtime client"
    )
    max_tokens: int = Field(
        default=2000,
        description="Maximum number of tokens in the response"
    )
    temperature: Optional[float] = Field(
        default=None,
        description="Optional temperature setting for the model"
    )

