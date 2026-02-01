# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Amazon Bedrock Temporal Samples demonstrates different approaches to orchestrating AI agents with Amazon Bedrock's AgentCore. The main use case is a **Finance Personal Assistant** with multiple implementation variants.

**Key Technologies:**
- **Temporal** - Durable execution platform for workflow orchestration
- **Strands Agents** - Framework for building LLM-powered agents
- **Amazon Bedrock** - Claude 3.5/3.7 Sonnet models for LLM capabilities
- **Amazon Bedrock AgentCore** - Serverless execution environment for deployment

## Project Structure

```
finance-personal-assistant/
├── temporal-orchestrator/           # Temporal workflow orchestrates agents (human-in-the-loop)
├── strands-orchestrator/            # Strands agent orchestrates agents (automatic flow)
└── temporal-orchestrator-and-budget-agent/  # (future variant)
```

## Sample Variants

### temporal-orchestrator
Uses Temporal workflows to orchestrate budget and financial analysis agents with human-in-the-loop (user confirms investment amount via signal).

**Run locally:**
```bash
cd finance-personal-assistant/temporal-orchestrator
uv run python -m temporal.worker        # Terminal 1
uv run python -m temporal.start_workflow # Terminal 2
```

**Required environment variables:**
```bash
export TEMPORAL_ADDRESS=us-east-1.aws.api.temporal.io:7233
export TEMPORAL_NAMESPACE=<your-namespace>
export TEMPORAL_API_KEY=<your-api-key>
```

### strands-orchestrator
Uses a Strands orchestrator agent to coordinate budget and financial analysis agents. The orchestrator decides when to chain agents based on the query (no human-in-the-loop).

**Run locally:**
```bash
cd finance-personal-assistant/strands-orchestrator
python -m agents.run_assistant
```

## Common Components

Both variants share:
- **Budget Agent** - Analyzes spending, creates budgets, provides financial health scores
- **Financial Analysis Agent** - Stock research, portfolio recommendations via yfinance
- **FinancialReport model** - Pydantic model for structured budget output
- **Utils** - AgentCore helpers, guardrails, message formatting

## Dependencies

```bash
# Install dependencies for a specific variant
cd finance-personal-assistant/<variant>
pip install -r requirements.txt

# Or use uv
uv sync
```

## Dev Tools

```bash
black .      # Format
flake8 .     # Lint
mypy .       # Type check
```

## AgentCore Deployment

Each variant has an `agentcore_setup.ipynb` notebook for deployment. The notebooks include TTL adjustment code for demos.

## Python Version

Requires Python 3.10+. Uses `uv` for package management.
