# ABOUTME: Entry point for running the financial assistant with human-in-the-loop.
# ABOUTME: Provides a multi-turn CLI where the agent asks for confirmation before investment analysis.

import sys
from .orchestrator_agent import orchestrator_agent


def main():
    """Run the financial assistant in multi-turn conversation mode."""
    print("=" * 60)
    print("Financial Personal Assistant (Human-in-the-Loop)")
    print("=" * 60)
    print("\nThis assistant will ask for your confirmation before")
    print("proceeding from budget analysis to investment recommendations.")
    print("\nCommands:")
    print("  'quit' or 'exit' - End the conversation")
    print("  'reset' - Clear conversation history and start fresh")
    print("\nExamples:")
    print("  - 'Create a financial plan for $6000/month income'")
    print("  - 'Analyze Apple stock performance'")
    print("  - 'Create a budget for someone earning $5000/month'")
    print()

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

        if query.lower() == 'reset':
            orchestrator_agent.messages.clear()
            print("Conversation history cleared. Starting fresh.\n")
            continue

        print()  # Blank line before response

        try:
            response = orchestrator_agent(prompt=query)
            print(f"Assistant: {response.message['content'][0]['text']}")
        except Exception as e:
            print(f"Error: {e}")

        print()  # Blank line after response


def single_turn(query: str) -> str:
    """
    Run a single query (for programmatic use or testing).
    Note: This doesn't maintain conversation state between calls.
    """
    response = orchestrator_agent(prompt=query)
    return response.message["content"][0]["text"]


if __name__ == "__main__":
    # Allow single query from command line for quick testing
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Query: {query}\n")
        print(single_turn(query))
    else:
        main()
