# ABOUTME: AgentCore entrypoint for the Strands-orchestrated financial assistant with HITL.
# ABOUTME: Routes incoming requests to the orchestrator agent, preserving conversation state.

import logging

from bedrock_agentcore import BedrockAgentCoreApp
from agents.orchestrator_agent import orchestrator_agent

app = BedrockAgentCoreApp()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.entrypoint
async def invoke(payload):
    """
    AgentCore entrypoint that invokes the orchestrator agent.

    The orchestrator agent maintains conversation history in its messages list.
    For HITL to work, subsequent requests must be handled by the same container
    so that the conversation state persists between turns.
    """
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

    # Check for reset command
    if query.strip().lower() == "reset":
        orchestrator_agent.messages.clear()
        logger.info("Conversation history cleared")
        return {"response": "Conversation history cleared. Ready for a new conversation."}

    logger.info(f"Processing query: {query}")
    logger.info(f"Current message history length: {len(orchestrator_agent.messages)}")

    # Call the orchestrator agent (maintains conversation history)
    response = orchestrator_agent(prompt=query)
    result = response.message["content"][0]["text"]

    logger.info(f"Query processed. Message history length: {len(orchestrator_agent.messages)}")
    return {"response": result}


if __name__ == "__main__":
    app.run()
