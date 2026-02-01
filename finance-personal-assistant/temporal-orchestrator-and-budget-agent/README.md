# Finance Personal Assistant - Temporal Orchestrator with OpenAI Budget Agent

This sample extends the [finance-personal-assistant](https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/02-use-cases/finance-personal-assistant) sample use case from the Amazon Bedrock AgentCore Samples repository.

This variant demonstrates a **hybrid agent architecture**:
- **Temporal** orchestrates the overall workflow with human-in-the-loop
- **Budget Agent** uses OpenAI Agents SDK with Temporal's durability integration (GPT-4o)
- **Financial Analysis Agent** uses Strands Agents with Bedrock (Claude)

## Architecture

```
FinancialAssistantWorkflow (Temporal)
│
├── BudgetAgentWorkflow (OpenAI Agents SDK + Temporal durability)
│   ├── calculate_budget (activity as tool)
│   ├── create_financial_chart (activity as tool)
│   └── calculator (activity as tool)
│
├── invoke_bedrock_model (format report)
│
├── [wait for signal: user confirms investment amount]
│
├── financial_analysis_activity (Strands Agent)
│
└── invoke_bedrock_model (format analysis)
```

The OpenAI Agents SDK integration with Temporal makes the budget agent's model calls and tool executions durable - if the worker crashes, execution resumes from the last checkpoint.

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

3. Export/Activate required AWS Credentials for Bedrock access

4. Set up OpenAI API key for the budget agent
```bash
export OPENAI_API_KEY=<your-openai-api-key>
```

5. Setup connectivity to Temporal Cloud
```bash
export TEMPORAL_ADDRESS=us-east-1.aws.api.temporal.io:7233
export TEMPORAL_NAMESPACE=<your temporal namespace>
export TEMPORAL_API_KEY=<your temporal API key>
```

### Run locally

From the `temporal-orchestrator-and-budget-agent` directory you will need two terminal windows.

0. Authenticate to AWS
```bash
aws sso login --profile <your profile>
```

1. Run the Temporal worker with
```bash
uv run python -m temporal.worker
```

2. Interact with the agent (in a second terminal window)
```bash
uv run python -m temporal.start_workflow
```

### Run on AgentCore

Running on AgentCore is done through the `agentcore_setup.ipynb` notebook.

#### Prerequisites

Set the following in an `.env` file at the root of `finance-personal-assistant`:
- `TEMPORAL_API_KEY`
- `OPENAI_API_KEY`

#### Get the Temporal Worker running

The worker is run on AgentCore - run each of the cells in the notebook. See the notebook for more information.

#### Interact with the agent

```bash
uv run python -m temporal.start_workflow
```

#### About the AgentCore deployment

AWS Bedrock AgentCore Runtime provides a serverless execution environment. The Temporal worker runs in a container that auto-scales.

Temporal's durability means workflows survive container restarts - if the container goes away, when it comes back, the agent picks up where it left off.

There is a cell in the notebook that sets the container idle timeout - useful for demos to show container lifecycle events.
