# Finance Personal Assistant - Strands Orchestrator

This sample uses a Strands agent as the orchestrator to coordinate multiple specialized agents. It is based on the [finance-personal-assistant](https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/02-use-cases/finance-personal-assistant) sample from the Amazon Bedrock AgentCore Samples repository.

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│   Orchestrator Agent (Strands)  │
│   - Routes to appropriate agent │
│   - Synthesizes responses       │
└─────────────────────────────────┘
    │                    │
    ▼                    ▼
┌──────────────┐  ┌─────────────────────┐
│ Budget Agent │  │ Financial Analysis  │
│   (tool)     │  │   Agent (tool)      │
└──────────────┘  └─────────────────────┘
```

The orchestrator agent decides which specialized agent(s) to call based on the user's query:
- **Budget Agent**: For budget analysis, spending habits, financial health assessment
- **Financial Analysis Agent**: For investment research, portfolio recommendations, stock analysis

For comprehensive queries, the orchestrator can chain both agents together.

## Demo

### Prerequisites

1. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

The `requirements.txt` at the root includes a few foundations that are used in this (and, eventually, other) samples.

```bash
pip install -r ../requirements.txt
```
And now the dependencies for this project

```bash
pip install -r requirements.txt
```

3. Export/Activate required AWS Credentials for the agents to access Bedrock

### Run locally

Run the assistant from the project root:

```bash
python -m agents.run_assistant
```

Or with a query directly:

```bash
python -m agents.run_assistant "Create a budget for someone earning $6000/month"
```

### Run on AgentCore

Running on AgentCore is done through the `agentcore_setup.ipynb` notebook.

#### Prerequisites

1. Register your virtual environment as a kernel for Jupyter notebook to use
```bash
python -m ipykernel install --user --name=notebook-venv --display-name="Python (notebook-venv)"
```

2. Run the notebook and ensure the correct kernel is selected
```bash
jupyter notebook agentcore_setup.ipynb
```

#### About the AgentCore deployment

AWS Bedrock AgentCore Runtime provides a serverless execution environment. The orchestrator agent runs in a container that auto-scales based on demand.

There is a cell in the notebook that allows you to adjust the container idle timeout - useful for demos to show container lifecycle events.
