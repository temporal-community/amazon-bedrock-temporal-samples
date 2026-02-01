# ABOUTME: AgentCore entrypoint for the Strands-orchestrated financial assistant.
# ABOUTME: Routes incoming requests to the orchestrator agent.

import logging

from bedrock_agentcore import BedrockAgentCoreApp
from agents.orchestrator_agent import orchestrator_agent

app = BedrockAgentCoreApp()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.entrypoint
async def invoke(payload):
    """AgentCore entrypoint that invokes the orchestrator agent."""
    logger.info(f"Received payload: {payload}")

    # Extract the query from the payload
    if isinstance(payload, dict):
        query = payload.get("query") or payload.get("prompt") or payload.get("message", "")
    elif isinstance(payload, str):
        query = payload
    else:
        query = str(payload)

    if not query:
        return {"error": "No query provided in payload"}

    logger.info(f"Processing query: {query}")

    # Call the orchestrator agent
    response = orchestrator_agent(prompt=query)
    result = response.message["content"][0]["text"]

    logger.info("Query processed successfully")
    return {"response": result}


if __name__ == "__main__":
    app.run()
