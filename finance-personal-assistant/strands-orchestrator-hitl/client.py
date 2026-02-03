# ABOUTME: Client for interacting with the AgentCore-deployed HITL financial assistant.
# ABOUTME: Runs a conversation loop, sending each message to the AgentCore endpoint.

import json
import os
import sys
import urllib.parse
import uuid
from typing import Optional

import boto3
import requests
from boto3.session import Session


def get_bearer_token(client_id: str, region: str = "us-west-2") -> str:
    """Authenticate and get a bearer token from Cognito."""
    cognito_client = boto3.client("cognito-idp", region_name=region)
    auth_response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": "testuser", "PASSWORD": "MyPassword123!"},
    )
    return auth_response["AuthenticationResult"]["AccessToken"]


def invoke_agent(
    agent_arn: str,
    query: str,
    session_id: str,
    bearer_token: str,
    region: str = "us-west-2",
) -> str:
    """Invoke the AgentCore endpoint with a query."""
    escaped_arn = urllib.parse.quote(agent_arn, safe="")
    url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{escaped_arn}/invocations"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
    }

    payload = {"query": query}

    response = requests.post(
        url,
        params={"qualifier": "DEFAULT"},
        headers=headers,
        json=payload,
        timeout=120,
    )

    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code} - {response.text}")

    result = response.json()
    return result.get("response", result)


def main():
    """Run the HITL financial assistant client."""
    import argparse

    parser = argparse.ArgumentParser(description="HITL Financial Assistant Client")
    parser.add_argument(
        "--session-id",
        help="Existing session ID to resume (default: generate new UUID)",
    )
    args = parser.parse_args()

    # Configuration - these should be set before running
    agent_arn = os.environ.get("AGENT_ARN")
    client_id = os.environ.get("COGNITO_CLIENT_ID")
    region = os.environ.get("AWS_REGION", "us-west-2")

    if not agent_arn:
        print("Error: AGENT_ARN environment variable not set")
        print("Set it with: export AGENT_ARN=<your-agent-arn>")
        sys.exit(1)

    if not client_id:
        print("Error: COGNITO_CLIENT_ID environment variable not set")
        print("Set it with: export COGNITO_CLIENT_ID=<your-cognito-client-id>")
        sys.exit(1)

    print("=" * 60)
    print("Financial Personal Assistant (Human-in-the-Loop)")
    print("Connected to AgentCore")
    print("=" * 60)
    print("\nThis assistant will ask for your confirmation before")
    print("proceeding from budget analysis to investment recommendations.")
    print("\nCommands:")
    print("  'quit' or 'exit' - End the conversation")
    print("  'reset' - Clear conversation history on the server")
    print("  'token' - Refresh the bearer token")
    print()

    # Get initial bearer token
    print("Authenticating...")
    try:
        bearer_token = get_bearer_token(client_id, region)
        print("Authentication successful.\n")
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    # Use provided session ID or generate a new one
    if args.session_id:
        session_id = args.session_id
        print(f"Resuming session: {session_id}\n")
    else:
        session_id = str(uuid.uuid4())
        print(f"New session ID: {session_id}")
        print("(Use --session-id to resume this session later)\n")

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue

        if query.lower() in ('quit', 'exit'):
            print("Goodbye!")
            break

        if query.lower() == 'token':
            print("Refreshing bearer token...")
            try:
                bearer_token = get_bearer_token(client_id, region)
                print("Token refreshed successfully.\n")
            except Exception as e:
                print(f"Token refresh failed: {e}\n")
            continue

        print()  # Blank line before response

        try:
            response = invoke_agent(
                agent_arn=agent_arn,
                query=query,
                session_id=session_id,
                bearer_token=bearer_token,
                region=region,
            )
            print(f"Assistant: {response}")
        except Exception as e:
            print(f"Error: {e}")
            print("Try 'token' command to refresh authentication.\n")

        print()  # Blank line after response


if __name__ == "__main__":
    main()
