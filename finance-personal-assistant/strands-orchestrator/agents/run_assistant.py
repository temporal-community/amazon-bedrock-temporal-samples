# ABOUTME: Entry point for running the financial assistant interactively.
# ABOUTME: Provides a simple CLI to interact with the orchestrator agent.

import sys
from .orchestrator_agent import orchestrator_agent


def main():
    """Run the financial assistant with a query."""
    # Get query from command line or prompt
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("=" * 60)
        print("Financial Personal Assistant")
        print("=" * 60)
        print("\nExamples:")
        print("  - 'Create a budget for someone earning $6000/month'")
        print("  - 'Analyze Apple stock performance'")
        print("  - 'Create a financial plan for $5000 monthly income with $800 dining expenses'")
        print()
        query = input("Enter your query: ").strip()

    if not query:
        print("No query provided. Exiting.")
        return

    print(f"\nProcessing: {query}\n")
    print("-" * 60)

    response = orchestrator_agent(prompt=query)
    print(response.message["content"][0]["text"])


if __name__ == "__main__":
    main()
