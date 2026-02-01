# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Amazon Bedrock Temporal Samples demonstrates orchestrating AI agents using Temporal with Amazon Bedrock's AgentCore. The main sample is a **Finance Personal Assistant** that uses Temporal workflows to coordinate multiple Strands-based AI agents.

**Key Technologies:**
- **Temporal** - Durable execution platform for workflow orchestration
- **Strands Agents** - Framework for building LLM-powered agents
- **Amazon Bedrock** - Claude 3.5/3.7 Sonnet models for LLM capabilities
- **Amazon Bedrock AgentCore** - Serverless execution environment for deployment

## Commands

### Local Development (from `finance-personal-assistant/temporal/` directory)

```bash
# Run the Temporal worker (Terminal 1)
uv run python -m temporal.worker

# Start/interact with workflow (Terminal 2)
uv run python -m temporal.start_workflow
```

### Dependencies

```bash
# Install root dependencies
pip install -r requirements.txt

# Install finance-personal-assistant dependencies
pip install -r finance-personal-assistant/requirements.txt
```

### Dev Tools

```bash
# Format code
black .

# Lint
flake8 .

# Type check
mypy .
```

### Required Environment Variables

```bash
export TEMPORAL_ADDRESS=us-east-1.aws.api.temporal.io:7233
export TEMPORAL_NAMESPACE=<your-namespace>
export TEMPORAL_API_KEY=<your-api-key>
```

## Architecture

### Workflow Orchestration Pattern

The system uses Temporal workflows to orchestrate multiple AI agent activities:

```
FinancialAssistantWorkflow
├── budget_agent_activity (Strands agent → FinancialReport)
├── invoke_bedrock_model (format budget report)
├── [wait for signal: investment amount from user]
├── financial_analysis_activity (Strands agent → portfolio analysis)
└── invoke_bedrock_model (format analysis)
```

### Key Components

**Temporal Layer** (`finance-personal-assistant/temporal/`):
- `financial_assistant_workflow.py` - Main workflow with signals/queries for user interaction
- `budget_agent_activity.py` - Strands agent for budget analysis, returns structured `FinancialReport`
- `financial_analysis_activity.py` - Strands agent for stock research via yfinance
- `llm_activity.py` - Generic Bedrock model invocation activity
- `models.py` - Pydantic models (`FinancialReport`, `BedrockInvocationRequest`)
- `worker.py` - Temporal worker entry point
- `start_workflow.py` - Client for starting workflows and sending signals

**Utils** (`finance-personal-assistant/utils/`):
- `message_formatter.py` - Conversation formatting
- `guardrail.py` - Bedrock guardrail management
- `agentcore_utils.py` - AgentCore helpers

### Temporal Patterns Used

- **Signals** - `set_investment_amount` signal allows external input during workflow execution
- **Queries** - `get_recommended_investment_amount` exposes workflow state
- **wait_condition** - Workflow pauses until signal received
- **Structured outputs** - Strands `structured_output()` with Pydantic models for type-safe agent responses

### AgentCore Deployment

The `agentcore_setup.ipynb` notebook handles deployment to AgentCore. The worker runs in a container that auto-scales. Container idle timeout considerations apply - Temporal's durability means workflows survive container restarts.

## Python Version

Requires Python 3.10+. Uses `uv` for package management.
