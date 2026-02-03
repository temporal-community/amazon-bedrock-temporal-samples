# Finance Personal Assistant - Strands Orchestrator with Human-in-the-Loop

This sample uses a Strands agent as the orchestrator to coordinate multiple specialized agents, with a **human-in-the-loop** pattern between the budget analysis and investment recommendation phases.

## How It Differs from strands-orchestrator

| Aspect | strands-orchestrator | strands-orchestrator-hitl |
|--------|---------------------|---------------------------|
| Flow | Automatic chaining | Asks for confirmation |
| User interaction | Single query, full response | Multi-turn conversation |
| Investment decision | Agent decides automatically | User confirms amount |

## Human-in-the-Loop Flow

1. User asks for a financial plan
2. Orchestrator calls the budget agent
3. Budget analysis is presented with a recommended investment amount
4. **Orchestrator asks user to confirm the investment amount**
5. User responds with their desired amount
6. Orchestrator calls the financial analysis agent with confirmed amount
7. Investment portfolio is presented to the user

## Important Limitations

- **Not durable**: Conversation state is in-memory. If the process dies, state is lost.
- **Requires active session**: User must remain connected during the conversation.
- **LLM-dependent**: The "ask before proceeding" relies on prompt instructions.

For durable human-in-the-loop workflows, see `temporal-orchestrator` which uses Temporal signals.

## Run Locally

```bash
# Install dependencies
uv sync

# Run the assistant
python -m agents.run_assistant
```

Commands in the CLI:
- `quit` or `exit` - End the conversation
- `reset` - Clear conversation history

## Deploy to AgentCore

Use the `agentcore_setup.ipynb` notebook to deploy to Amazon Bedrock AgentCore.

After deployment, use the CLI client to interact with the deployed agent:

```bash
export AGENT_ARN='<your-agent-arn>'
export COGNITO_CLIENT_ID='<your-cognito-client-id>'
python client.py
```

The notebook will print these values after deployment.

## Project Files

| File | Purpose |
|------|---------|
| `agents/run_assistant.py` | Local CLI with conversation loop |
| `worker.py` | AgentCore entrypoint |
| `client.py` | CLI client for AgentCore deployment |
| `agentcore_setup.ipynb` | Deployment notebook |

## See Also

- `docs/research/human-in-the-loop-approaches.md` - Detailed analysis of HITL approaches
