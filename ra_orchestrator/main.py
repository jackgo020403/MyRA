"""Main CLI entrypoint for RA Orchestrator."""
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

from ra_orchestrator.graph import RAOrchestrator


def main():
    """Main CLI entrypoint."""
    # Load environment variables
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key.")
        print("See .env.example for reference.")
        sys.exit(1)

    # Get research question from command line or user input
    if len(sys.argv) > 1:
        # Command-line argument provided
        research_question = " ".join(sys.argv[1:]).strip()
    else:
        # Interactive mode
        print("\n" + "=" * 80)
        print("RESEARCH ASSISTANT ORCHESTRATOR")
        print("Milestone 3: Synthesis & Memo")
        print("=" * 80)
        print("\nThis tool will:")
        print("  1. Create a research plan from your question")
        print("  2. Ask for your approval")
        print("  3. Perform web research with quality filters")
        print("  4. Generate synthesis and executive memo")
        print("  5. Create final Excel with MEMO, SYNTHESIS, and RAW DATA tabs")
        print("\n")

        research_question = input("Enter your research question: ").strip()

    if not research_question:
        print("Error: Research question cannot be empty.")
        sys.exit(1)

    # Set up output directory
    output_dir = Path(__file__).parent.parent / "outputs"

    # Run orchestrator
    orchestrator = RAOrchestrator(api_key=api_key, output_dir=output_dir)

    try:
        final_state = orchestrator.run(research_question)

        if final_state["current_phase"] == "m3_complete":
            print(f"\n✓ Success! Final Excel file:")
            print(f"  {final_state['excel_path']}")
        elif final_state["current_phase"] == "dry_run_complete":
            print(f"\nDry-run complete. Check your Excel file at:")
            print(f"  {final_state['excel_path']}")
        else:
            print(f"\nWorkflow ended at phase: {final_state['current_phase']}")

    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
